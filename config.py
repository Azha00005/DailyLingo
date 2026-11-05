"""Все настройки читаются из файла .env рядом с ботом."""
import os

from dotenv import load_dotenv

load_dotenv()


def _required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise SystemExit(f"Не задана переменная {name} в .env")
    return value


# Telegram
TELEGRAM_TOKEN = _required("TELEGRAM_BOT_TOKEN")
OWNER_ID = int(_required("OWNER_ID"))  # бот отвечает только вам

# Groq: распознавание речи + основная LLM
GROQ_API_KEY = _required("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "whisper-large-v3-turbo")

# Gemini: запасная LLM (необязательно)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")

# Обучение
LEVEL = os.getenv("LEVEL", "A2-B1")
INTERESTS = os.getenv("INTERESTS", "science, culture, psychology")
NATIVE_LANGUAGE = os.getenv("NATIVE_LANGUAGE", "Russian")  # язык переводов и объяснений
UI_LANG = os.getenv("UI_LANG", "en")                       # язык интерфейса: en / ru

# Расписание
TIMEZONE = os.getenv("TIMEZONE", "UTC")
DIGEST_TIME = os.getenv("DIGEST_TIME", "08:00")
DIGEST_SIZE = int(os.getenv("DIGEST_SIZE", "5"))
REVIEW_DAY = os.getenv("REVIEW_DAY", "sun")
REVIEW_TIME = os.getenv("REVIEW_TIME", "11:00")

# Озвучка
VOICE_REPLIES = os.getenv("VOICE_REPLIES", "1") == "1"
TTS_VOICE = os.getenv("TTS_VOICE", "en-US-AriaNeural")
TTS_RATE = os.getenv("TTS_RATE", "-5%")

# Контент
FEEDS_FILE = os.getenv("FEEDS_FILE", "feeds.txt")
MAX_AGE_HOURS = int(os.getenv("MAX_AGE_HOURS", "48"))
PODCAST_MAX_MB = int(os.getenv("PODCAST_MAX_MB", "9"))  # ≈ первые 10 минут выпуска
TEXT_LIMIT = 8000  # символов текста материала, которые уходят в LLM

DB_PATH = os.getenv("DB_PATH", "english_bot.db")
