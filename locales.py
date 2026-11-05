"""Тексты интерфейса. Язык выбирается переменной UI_LANG (ru / en).
Чтобы добавить язык, скопируйте блок "en" и переведите значения."""
from config import UI_LANG

STRINGS: dict[str, dict[str, str]] = {
    "en": {
        "start": (
            "Hi! I help you learn English with materials on topics you care about.\n\n"
            "☀️ Every day at {time}: a digest.\n"
            "📖 <b>Simplify</b> — a B1-level retelling\n"
            "📚 <b>Words</b> — a word list and a block to import into Quizlet\n"
            "🎙 <b>Discuss</b> — a voice conversation with corrections after every reply\n"
            "🗓 Every week: a review of your typical mistakes\n\n"
            "/digest — digest now\n/review — mistakes review now\n/end — finish the discussion"
        ),
        "btn_simple": "📖 Simplify",
        "btn_words": "📚 Words",
        "btn_talk": "🎙 Discuss",
        "btn_open": "🔗 Open",
        "digest_collecting": "Collecting the digest, this takes about a minute…",
        "digest_failed": "⚠️ Could not build the digest: {error}",
        "digest_empty": "No new materials today. Check the feeds in feeds.txt.",
        "digest_header": "☀️ <b>Today's digest</b>: {count} materials",
        "review_few": "Not enough mistakes this week for a review yet. Keep talking 💪",
        "review_failed": "⚠️ Could not build the review: {error}",
        "review_empty": "⚠️ Could not build the review. Try /review later.",
        "review_header": "🗓 <b>Weekly mistakes review</b>: {count} corrections",
        "review_exercises": "<b>Exercises</b> (answers under the spoiler):",
        "end_none": "There is no active discussion.",
        "end_done": "Discussion finished.",
        "end_header": "🏁 <b>Discussion summary</b>",
        "end_fallback": "Discussion finished, great job!",
        "phrases_header": "<b>Useful expressions:</b>",
        "quizlet_header": "📋 <b>For Quizlet</b> (tap the block to copy; separator «|»):",
        "item_missing": "Material not found.",
        "note_simple": "Preparing a retelling…",
        "note_words": "Picking words…",
        "note_talk": "Starting the discussion…",
        "words_failed": "Could not pick words. Please try again.",
        "talk_header": "🎙 <b>Discussing:</b> {title}\nReply with voice or text messages. Finish — /end",
        "not_heard": "I didn't catch that 🙈 Please try again.",
        "talk_missing": "Material not found, the discussion is over.",
        "hint": "To talk, tap «🎙 Discuss» under a material from the digest. Digest right now — /digest",
        "corr_header": "✏️ <b>Corrections</b>",
        "corr_none": "✅ No mistakes!",
        "corr_ok": "✅ No mistakes.",
        "corr_better": "💡 <b>More natural:</b> {text}",
        "error": "⚠️ Something went wrong: {error}",
        "cmd_digest": "Digest now",
        "cmd_review": "Weekly mistakes review",
        "cmd_end": "Finish the discussion",
        "link_removed": "[link removed]",
    },
    "ru": {
        "start": (
            "Привет! Я помогаю учить английский на материалах по вашим интересам.\n\n"
            "☀️ Каждый день в {time} — дайджест.\n"
            "📖 <b>Упростить</b> — пересказ на уровне B1\n"
            "📚 <b>Слова</b> — список слов и блок для импорта в Quizlet\n"
            "🎙 <b>Обсудить</b> — разговор голосовыми, исправления после каждой реплики\n"
            "🗓 Раз в неделю — разбор ваших ошибок\n\n"
            "/digest — дайджест сейчас\n/review — разбор ошибок сейчас\n/end — закончить обсуждение"
        ),
        "btn_simple": "📖 Упростить",
        "btn_words": "📚 Слова",
        "btn_talk": "🎙 Обсудить",
        "btn_open": "🔗 Открыть",
        "digest_collecting": "Собираю дайджест, это займёт минуту…",
        "digest_failed": "⚠️ Дайджест не собрался: {error}",
        "digest_empty": "Сегодня новых материалов не нашлось. Проверьте ленты в feeds.txt.",
        "digest_header": "☀️ <b>Дайджест на сегодня</b>: {count} материалов",
        "review_few": "За неделю пока мало ошибок для разбора. Продолжайте обсуждения 💪",
        "review_failed": "⚠️ Разбор ошибок не получился: {error}",
        "review_empty": "⚠️ Не получилось составить разбор. Попробуйте /review позже.",
        "review_header": "🗓 <b>Разбор ошибок за неделю</b>: {count} исправлений",
        "review_exercises": "<b>Упражнения</b> (ответ под спойлером):",
        "end_none": "Сейчас нет активного обсуждения.",
        "end_done": "Обсуждение закончено.",
        "end_header": "🏁 <b>Итог обсуждения</b>",
        "end_fallback": "Обсуждение закончено, отличная работа!",
        "phrases_header": "<b>Полезные выражения:</b>",
        "quizlet_header": "📋 <b>Для Quizlet</b> (нажмите на блок, чтобы скопировать; разделитель «|»):",
        "item_missing": "Материал не найден.",
        "note_simple": "Готовлю пересказ…",
        "note_words": "Подбираю слова…",
        "note_talk": "Начинаем обсуждение…",
        "words_failed": "Не получилось подобрать слова. Попробуйте ещё раз.",
        "talk_header": "🎙 <b>Обсуждаем:</b> {title}\nОтвечайте голосовыми или текстом. Закончить — /end",
        "not_heard": "Не расслышал 🙈 Попробуйте ещё раз.",
        "talk_missing": "Материал не найден, обсуждение закончено.",
        "hint": "Чтобы поговорить, нажмите «🎙 Обсудить» под материалом из дайджеста. Дайджест прямо сейчас — /digest",
        "corr_header": "✏️ <b>Исправления</b>",
        "corr_none": "✅ Без ошибок!",
        "corr_ok": "✅ Ошибок нет.",
        "corr_better": "💡 <b>Естественнее:</b> {text}",
        "error": "⚠️ Что-то пошло не так: {error}",
        "cmd_digest": "Дайджест сейчас",
        "cmd_review": "Разбор ошибок за неделю",
        "cmd_end": "Закончить обсуждение",
        "link_removed": "[ссылка удалена]",
    },
}


def t(key: str, **kwargs) -> str:
    table = STRINGS.get(UI_LANG, STRINGS["en"])
    template = table.get(key) or STRINGS["en"][key]
    return template.format(**kwargs) if kwargs else template
