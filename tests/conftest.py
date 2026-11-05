import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

os.environ.setdefault("TELEGRAM_BOT_TOKEN", "123456789:AAFakeTokenForTestsOnly_abcdefghijk")
os.environ.setdefault("OWNER_ID", "42")
os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("UI_LANG", "en")
os.environ["DB_PATH"] = str(ROOT / "tests" / "_test.db")
