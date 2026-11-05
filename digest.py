"""Сбор свежих материалов из RSS, извлечение текста статей и начала подкастов."""
import calendar
import html
import logging
import re
import time
from urllib.parse import urljoin

import feedparser
import trafilatura

import net
from config import FEEDS_FILE, MAX_AGE_HOURS, PODCAST_MAX_MB, TEXT_LIMIT

log = logging.getLogger("digest")
FEED_MAX_BYTES = 5 * 1024 * 1024
ARTICLE_MAX_BYTES = 3 * 1024 * 1024


def _clean(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text or "")
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def read_feeds() -> list[tuple[str, str]]:
    """feeds.txt: «категория | ссылка» или просто ссылка; строки с # пропускаются."""
    feeds = []
    with open(FEEDS_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "|" in line:
                category, url = (part.strip() for part in line.split("|", 1))
            else:
                category, url = "other", line
            feeds.append((category, url))
    return feeds


def _discover_feed(page: bytes, base_url: str) -> str | None:
    """Ищет в HTML-странице ссылку на RSS/Atom: <link rel="alternate" type="application/rss+xml" href=...>."""
    text = page[:300_000].decode("utf-8", "ignore")
    for tag in re.findall(r"<link\b[^>]*>", text, re.I):
        if (re.search(r"rel=[\"']?alternate", tag, re.I)
                and re.search(r"type=[\"']?application/(?:rss|atom)\+xml", tag, re.I)):
            match = re.search(r"href=[\"']([^\"']+)[\"']", tag, re.I)
            if match:
                return urljoin(base_url, html.unescape(match.group(1)))
    return None


def _load_feed(url: str):
    """Загружает ленту. Если по адресу оказалась обычная страница сайта — пробует найти на ней ленту."""
    data = net.fetch(url, FEED_MAX_BYTES)
    feed = feedparser.parse(data)
    if feed.entries:
        return feed
    found = _discover_feed(data, url)
    if found and found != url:
        log.info("По адресу %s найдена лента %s — впишите её в feeds.txt", url, found)
        feed = feedparser.parse(net.fetch(found, FEED_MAX_BYTES))
    if not feed.entries:
        log.warning("В %s нет записей: это не RSS-лента? Нужен адрес именно ленты (feed / rss).", url)
    return feed


def fetch_candidates() -> list[dict]:
    """Свежие записи из всех лент, новые сверху. Синхронно — вызывать через asyncio.to_thread."""
    cutoff = time.time() - MAX_AGE_HOURS * 3600
    out = []
    for category, feed_url in read_feeds():
        try:
            feed = _load_feed(feed_url)
        except Exception as exc:  # noqa: BLE001 — одна сломанная лента не должна ронять дайджест
            log.warning("Лента %s недоступна: %s", feed_url, exc)
            continue
        for entry in feed.entries[:30]:
            parsed = entry.get("published_parsed") or entry.get("updated_parsed")
            ts = calendar.timegm(parsed) if parsed else 0
            if ts and ts < cutoff:
                continue
            audio = next(
                (enc.get("href") for enc in entry.get("enclosures", [])
                 if (enc.get("type") or "").startswith("audio") and enc.get("href")),
                None,
            )
            if audio and not audio.startswith(("http://", "https://")):
                audio = None
            link = entry.get("link") or audio
            if not link or not link.startswith(("http://", "https://")):
                continue
            out.append({
                "url": link,
                "title": _clean(entry.get("title", "")) or "(без названия)",
                "category": category,
                "kind": "podcast" if audio else "article",
                "audio_url": audio,
                "description": _clean(entry.get("summary", ""))[:1500],
                "ts": ts,
            })
    out.sort(key=lambda c: c["ts"], reverse=True)
    return out


def extract_article(url: str) -> str:
    """Чистый текст статьи. Синхронно — вызывать через asyncio.to_thread."""
    page = net.fetch(url, ARTICLE_MAX_BYTES)
    text = trafilatura.extract(page) if page else None
    return (text or "")[:TEXT_LIMIT]


def download_audio_head(url: str) -> bytes:
    """Только начало выпуска (PODCAST_MAX_MB), чтобы уложиться в лимиты Whisper.
    Синхронно — вызывать через asyncio.to_thread."""
    return net.fetch(url, PODCAST_MAX_MB * 1024 * 1024, truncate=True, deadline=180, timeout=60)