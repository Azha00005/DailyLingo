"""DailyLingo — a self-hosted Telegram bot for learning English.

Interest-based digest → 📖 simplify / 📚 words for Quizlet / 🎙 voice discussion
with corrections after every reply. On Sundays — a weekly review of your mistakes.
Run: python bot.py
"""
import asyncio
import html
import logging
import os
import re
from urllib.parse import urlparse

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    BotCommand,
    BufferedInputFile,
    CallbackQuery,
    ErrorEvent,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from aiogram.utils.chat_action import ChatActionSender
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

import ai
import db
import digest
import tts
from config import (
    DIGEST_SIZE,
    DIGEST_TIME,
    OWNER_ID,
    REVIEW_DAY,
    REVIEW_TIME,
    TELEGRAM_TOKEN,
    TEXT_LIMIT,
    TIMEZONE,
    VOICE_REPLIES,
)
from locales import t

log = logging.getLogger("bot")
router = Router()
# The bot is for you only and only in a private chat: other users and groups are ignored
router.message.filter(F.from_user.id == OWNER_ID, F.chat.type == "private")
router.callback_query.filter(F.from_user.id == OWNER_ID, F.message.chat.type == "private")

HISTORY_LIMIT = 12  # how many recent discussion turns the bot remembers


class Talk(StatesGroup):
    active = State()


# ======================= formatting =======================
def esc(value) -> str:
    return html.escape(str(value or ""), quote=False)


def md_bold(text: str) -> str:
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", esc(text))


def words_list(cards: list[dict]) -> str:
    lines = []
    for c in cards:
        lines.append(f"• <b>{esc(c['term'])}</b> — {esc(c['translation'])}")
        if c["example"]:
            lines.append(f"   <i>{esc(c['example'])}</i>")
    return "\n".join(lines)


def quizlet_block(cards: list[dict]) -> str:
    """Lines like "word|translation — example" for Quizlet import with the | separator."""
    def field(s: str) -> str:
        return s.replace("|", "/").replace("\n", " ").strip()

    rows = []
    for c in cards:
        definition = field(c["translation"])
        if c["example"]:
            definition += f" — {field(c['example'])}"
        rows.append(f"{field(c['term'])}|{definition}")
    return "<pre>" + esc("\n".join(rows)) + "</pre>"


def corrections_text(corrections: list[dict], better: str) -> str:
    if not corrections and not better:
        return t("corr_none")
    lines = [t("corr_header")] if corrections else [t("corr_ok")]
    for c in corrections:
        lines.append(f"• <s>{esc(c['original'])}</s> → <b>{esc(c['corrected'])}</b>")
        if c.get("explanation"):
            lines.append(f"   {esc(c['explanation'])}")
    if better:
        lines.append("\n" + t("corr_better", text=esc(better)))
    return "\n".join(lines)


def card_text(item: dict) -> str:
    icon = "🎧" if item["kind"] == "podcast" else "📰"
    text = f"{icon} <b>{esc(item['title'])}</b>\n<code>{esc(item['category'])}</code>"
    if item.get("blurb"):
        text += f"\n<i>{esc(item['blurb'])}</i>"
    return text


def item_keyboard(item: dict) -> InlineKeyboardMarkup:
    i = item["id"]
    second_row = [InlineKeyboardButton(text=t("btn_talk"), callback_data=f"talk:{i}")]
    if item["url"].startswith(("http://", "https://")):
        second_row.append(InlineKeyboardButton(text=t("btn_open"), url=item["url"]))
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("btn_simple"), callback_data=f"simple:{i}"),
         InlineKeyboardButton(text=t("btn_words"), callback_data=f"words:{i}")],
        second_row,
    ])


async def send_long(bot: Bot, text: str) -> None:
    """Splits long text by paragraph to fit the Telegram limit (4096 characters)."""
    chunks, current = [], ""
    for part in text.split("\n\n"):
        candidate = f"{current}\n\n{part}" if current else part
        if len(candidate) <= 4000:
            current = candidate
            continue
        if current:
            chunks.append(current)
        while len(part) > 4000:  # emergency split of a very long paragraph
            cut = part.rfind("\n", 0, 4000)
            cut = cut if cut > 0 else 4000
            chunks.append(part[:cut])
            part = part[cut:]
        current = part
    if current:
        chunks.append(current)
    for chunk in chunks:
        await bot.send_message(OWNER_ID, chunk)


async def send_voice_reply(bot: Bot, text: str) -> None:
    if not VOICE_REPLIES or not text:
        return
    try:
        audio = await tts.synthesize(text)
        if audio:
            await bot.send_voice(OWNER_ID, BufferedInputFile(audio, "reply.mp3"))
    except Exception:  # noqa: BLE001 — the discussion works without voice anyway
        log.exception("Text-to-speech failed")


def typing(bot: Bot):
    return ChatActionSender.typing(bot=bot, chat_id=OWNER_ID)


# ======================= materials =======================
async def ensure_text(item: dict) -> str:
    """Article text or transcript of the start of a podcast; saved to the DB."""
    if item["text"]:
        return item["text"]
    text = ""
    try:
        if item["kind"] == "podcast" and item["audio_url"]:
            ext = os.path.splitext(urlparse(item["audio_url"]).path)[1] or ".mp3"
            audio = await asyncio.to_thread(digest.download_audio_head, item["audio_url"])
            text = await ai.transcribe(audio, f"episode{ext}")
        else:
            text = await asyncio.to_thread(digest.extract_article, item["url"])
    except Exception:  # noqa: BLE001
        log.exception("Failed to get the text of material %s", item["url"])
    text = (text or item["description"] or item["title"])[:TEXT_LIMIT]
    db.update_item(item["id"], text=text)
    item["text"] = text
    return text


async def ensure_summary(item: dict) -> str:
    if item["summary"]:
        return item["summary"]
    summary = await ai.summarize(await ensure_text(item))
    db.update_item(item["id"], summary=summary)
    item["summary"] = summary
    return summary


async def build_digest() -> list[dict]:
    candidates = await asyncio.to_thread(digest.fetch_candidates)
    seen = db.seen_urls()
    unique: dict[str, dict] = {}
    for c in candidates:
        if c["url"] not in seen and c["url"] not in unique:
            unique[c["url"]] = c
    candidates = list(unique.values())[:60]
    if not candidates:
        return []
    items = []
    for idx, blurb in await ai.pick_items(candidates, DIGEST_SIZE):
        c = candidates[idx]
        item_id = db.add_item(url=c["url"], title=c["title"], category=c["category"], kind=c["kind"],
                              audio_url=c["audio_url"], description=c["description"], blurb=blurb)
        items.append(db.get_item(item_id))
    return items


async def send_digest(bot: Bot) -> None:
    try:
        async with typing(bot):
            items = await build_digest()
    except Exception as exc:  # noqa: BLE001
        log.exception("Digest failed")
        await bot.send_message(OWNER_ID, t("digest_failed", error=esc(exc)))
        return
    if not items:
        await bot.send_message(OWNER_ID, t("digest_empty"))
        return
    await bot.send_message(OWNER_ID, t("digest_header", count=len(items)))
    for item in items:
        await bot.send_message(OWNER_ID, card_text(item), reply_markup=item_keyboard(item))


async def send_review(bot: Bot, manual: bool = False) -> None:
    errors = db.errors_since(7)
    if len(errors) < 3:
        if manual:
            await bot.send_message(OWNER_ID, t("review_few"))
        return
    try:
        async with typing(bot):
            result = await ai.weekly_review(errors[-60:])
    except Exception as exc:  # noqa: BLE001
        log.exception("Mistake review failed")
        await bot.send_message(OWNER_ID, t("review_failed", error=esc(exc)))
        return
    topics = [t for t in result.get("topics") or [] if isinstance(t, dict) and t.get("title")]
    if not topics:
        await bot.send_message(OWNER_ID, t("review_empty"))
        return
    await bot.send_message(OWNER_ID, t("review_header", count=len(errors)))
    for topic in topics:
        parts = [f"📘 <b>{esc(ai.sanitize(topic['title'], 200))}</b>",
                 esc(ai.sanitize(topic.get("explanation"), 2500))]
        exercises = [e for e in topic.get("exercises") or [] if isinstance(e, dict) and e.get("task")]
        if exercises:
            lines = [t("review_exercises")]
            for n, ex in enumerate(exercises, 1):
                task = esc(ai.sanitize(ex["task"], 400))
                answer = esc(ai.sanitize(ex.get("answer"), 400) or "—")
                lines.append(f"{n}. {task}\n   <tg-spoiler>{answer}</tg-spoiler>")
            parts.append("\n".join(lines))
        await send_long(bot, "\n\n".join(parts))


# ======================= commands =======================
@router.message(CommandStart())
async def on_start(message: Message) -> None:
    await message.answer(t("start", time=DIGEST_TIME))


@router.message(Command("digest"))
async def on_digest(message: Message, bot: Bot) -> None:
    await message.answer(t("digest_collecting"))
    await send_digest(bot)


@router.message(Command("review"))
async def on_review(message: Message, bot: Bot) -> None:
    await send_review(bot, manual=True)


@router.message(Command("end"))
async def on_end(message: Message, state: FSMContext, bot: Bot) -> None:
    if await state.get_state() != Talk.active.state:
        await message.answer(t("end_none"))
        return
    data = await state.get_data()
    await state.clear()
    history = data.get("history", [])
    item = db.get_item(data["item_id"])
    if len(history) < 3 or not item:
        await message.answer(t("end_done"))
        return
    async with typing(bot):
        result = await ai.wrap_up(item["title"], history)
    feedback = ai.sanitize(result.get("feedback"), 1500) or t("end_fallback")
    text = f"{t('end_header')}\n{esc(feedback)}"
    phrases = ai.clean_cards(result.get("phrases"), limit=8)
    if phrases:
        text += (f"\n\n{t('phrases_header')}\n{words_list(phrases)}"
                 f"\n\n{t('quizlet_header')}\n{quizlet_block(phrases)}")
    await send_long(bot, text)


# ======================= buttons under a material =======================
async def _item_from_callback(cb: CallbackQuery, note: str) -> dict | None:
    await cb.answer(note)
    item = db.get_item(int(cb.data.split(":", 1)[1]))
    if not item and cb.message:
        await cb.message.answer(t("item_missing"))
    return item


@router.callback_query(F.data.startswith("simple:"))
async def on_simple(cb: CallbackQuery, bot: Bot) -> None:
    item = await _item_from_callback(cb, t("note_simple"))
    if not item:
        return
    if not item["simple"]:
        async with typing(bot):
            simple = await ai.simplify(await ensure_text(item))
        db.update_item(item["id"], simple=simple)
        item["simple"] = simple
    await send_long(bot, f"📖 <b>{esc(item['title'])}</b>\n\n{md_bold(item['simple'])}")


@router.callback_query(F.data.startswith("words:"))
async def on_words(cb: CallbackQuery, bot: Bot) -> None:
    item = await _item_from_callback(cb, t("note_words"))
    if not item:
        return
    async with typing(bot):
        words = await ai.extract_words(await ensure_text(item))
    if not words:
        await bot.send_message(OWNER_ID, t("words_failed"))
        return
    await send_long(bot,
                    f"📚 <b>{esc(item['title'])}</b>\n\n{words_list(words)}"
                    f"\n\n{t('quizlet_header')}"
                    f"\n{quizlet_block(words)}")


@router.callback_query(F.data.startswith("talk:"))
async def on_talk(cb: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    item = await _item_from_callback(cb, t("note_talk"))
    if not item:
        return
    async with typing(bot):
        summary = await ensure_summary(item)
        question = await ai.opening_question(item["title"], summary)
    await state.set_state(Talk.active)
    await state.update_data(item_id=item["id"], history=[{"role": "assistant", "content": question}])
    await bot.send_message(
        OWNER_ID,
        f"{t('talk_header', title=esc(item['title']))}\n\n{esc(question)}",
    )
    await send_voice_reply(bot, question)


# ======================= discussion =======================
async def process_turn(message: Message, state: FSMContext, bot: Bot, user_text: str) -> None:
    user_text = user_text.strip()
    if not user_text:
        await message.answer(t("not_heard"))
        return
    data = await state.get_data()
    item = db.get_item(data["item_id"])
    if not item:
        await state.clear()
        await message.answer(t("talk_missing"))
        return
    history = data.get("history", [])

    async with typing(bot):
        summary = await ensure_summary(item)
        result = await ai.talk_turn(item["title"], summary, history, user_text)

    reply = ai.sanitize(result.get("reply"), 1200) or "Interesting! Tell me more."
    corrections = [
        {"original": ai.sanitize(c["original"], 300), "corrected": ai.sanitize(c["corrected"], 300),
         "explanation": ai.sanitize(c.get("explanation"), 400)}
        for c in (result.get("corrections") or [])[:5]
        if isinstance(c, dict) and c.get("original") and c.get("corrected")
        and str(c["original"]).strip().lower() != str(c["corrected"]).strip().lower()
    ]
    better = ai.sanitize(result.get("better"), 600)
    if better.lower().strip(" .!?") == user_text.lower().strip(" .!?"):
        better = ""

    if message.voice:
        await message.answer(f"🗣 <i>{esc(user_text)}</i>")  # what Whisper recognized
    await message.answer(esc(reply))
    await send_voice_reply(bot, reply)
    await message.answer(corrections_text(corrections, better))

    db.add_errors(item["id"], corrections)
    history = (history + [{"role": "user", "content": user_text},
                          {"role": "assistant", "content": reply}])[-HISTORY_LIMIT:]
    await state.update_data(history=history)


@router.message(Talk.active, F.voice)
async def on_talk_voice(message: Message, state: FSMContext, bot: Bot) -> None:
    async with typing(bot):
        buf = await bot.download(message.voice)
        text = await ai.transcribe(buf.getvalue(), "voice.ogg")
    await process_turn(message, state, bot, text)


@router.message(Talk.active, F.text & ~F.text.startswith("/"))
async def on_talk_text(message: Message, state: FSMContext, bot: Bot) -> None:
    await process_turn(message, state, bot, message.text)


@router.message(F.voice | F.text)
async def on_other(message: Message) -> None:
    await message.answer(t("hint"))


# ======================= startup =======================
async def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)  # don't log request URLs
    db.init()
    bot = Bot(TELEGRAM_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML,
                                                            link_preview_is_disabled=True))
    dp = Dispatcher()
    dp.include_router(router)

    async def on_error(event: ErrorEvent) -> bool:
        log.exception("Update handling error", exc_info=event.exception)
        try:
            await bot.send_message(OWNER_ID, t("error", error=esc(event.exception)[:300]))
        except Exception:  # noqa: BLE001
            pass
        return True

    dp.errors.register(on_error)

    digest_h, digest_m = map(int, DIGEST_TIME.split(":"))
    review_h, review_m = map(int, REVIEW_TIME.split(":"))
    scheduler = AsyncIOScheduler(timezone=TIMEZONE)
    scheduler.add_job(send_digest, CronTrigger(hour=digest_h, minute=digest_m, timezone=TIMEZONE),
                      args=[bot], misfire_grace_time=3600)
    scheduler.add_job(send_review, CronTrigger(day_of_week=REVIEW_DAY, hour=review_h, minute=review_m,
                                               timezone=TIMEZONE),
                      args=[bot], misfire_grace_time=3600)
    scheduler.start()

    await bot.set_my_commands([
        BotCommand(command="digest", description=t("cmd_digest")),
        BotCommand(command="review", description=t("cmd_review")),
        BotCommand(command="end", description=t("cmd_end")),
    ])
    log.info("Bot started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
