# DailyLingo

**Learn English from content you actually want to read.** A self-hosted Telegram bot that sends you a daily digest of articles and podcasts on your interests, turns any of them into vocabulary for Quizlet, and lets you discuss it by voice — with corrections after every reply.

[Русская версия](README.ru.md)

> Built for A2–B1 learners. Runs for $0/month on free API tiers and a free cloud VM.

## Features
- ☀️ **Daily digest** — 5 fresh articles and podcasts from *your* RSS feeds, picked by an LLM to match your interests, each with a level-friendly one-line description.
- 📖 **Simplify** — a B1-level retelling of any material, key words in bold.
- 📚 **Words** — 10–15 useful words and expressions from the material, with translations, examples and a ready-to-paste block for Quizlet import.
- 🎙 **Discuss** — talk about the material in voice messages. After every reply the bot shows what it heard, answers (text + voice), and lists your mistakes with short explanations and a more natural phrasing.
- 🗓 **Weekly review** — your typical mistakes grouped by topic, explained, with exercises built from your own sentences.

## How it works
```
RSS feeds ──► digest.py ──► LLM picks 5 items ──► Telegram digest
                                              ├─ 📖 Simplify  ─► LLM
                                              ├─ 📚 Words     ─► LLM ─► Quizlet import block
                                              └─ 🎙 Discuss   ─► Groq Whisper ─► LLM ─► reply + corrections
mistakes ─► SQLite ─► weekly review
```
| Part | Service | Cost |
|---|---|---|
| Speech-to-text | Groq Whisper | free tier |
| LLM | Groq (Llama 3.3 70B), optional Gemini fallback | free tier |
| Voice replies | edge-tts | free (see [Limitations](#limitations)) |
| Storage | SQLite | — |
| Hosting | any machine; e.g. Oracle Cloud Always Free | free |

## Quick start

### 1. Get the keys (5 minutes)
1. **Bot token** — message [@BotFather](https://t.me/BotFather) → `/newbot`. Then `/setjoingroups` → **Disable**.
2. **Your Telegram ID** — message [@userinfobot](https://t.me/userinfobot). The bot answers only this ID.
3. **Groq API key** — [console.groq.com](https://console.groq.com) → API Keys.
4. *(optional)* **Gemini API key** — [aistudio.google.com](https://aistudio.google.com) → Get API key.

### 2. Configure
```bash
git clone https://github.com/Azha00005/DailyLingo.git && cd DailyLingo
cp .env.example .env      # fill in the token, your ID and keys
```
Put your feeds into `feeds.txt`, one per line: `category | https://site.com/feed`.

### 3. Run
**Locally (Windows / macOS / Linux, Python 3.11+):**
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python bot.py
```
**Docker:**
```bash
mkdir -p data && sudo chown 10001 data   # the container runs as an unprivileged user
docker compose up -d --build
```
**Linux server with systemd:** see [english-bot.service](english-bot.service) (sandboxed unit) and the server section in [README.ru.md](README.ru.md#4-сервер-247-oracle-cloud-always-free-ubuntu).

Then send `/start` and `/digest` to your bot.

> Run the bot in **one place only** — two copies with the same token cause a Telegram `Conflict` error.

## Configuration
All settings live in `.env` (see [.env.example](.env.example)).

| Variable | Default | Meaning |
|---|---|---|
| `UI_LANG` | `en` | interface language: `en`, `ru` |
| `NATIVE_LANGUAGE` | `Russian` | language for translations and explanations |
| `LEVEL` | `A2-B1` | your English level |
| `INTERESTS` | `science, culture, psychology` | what the digest should pick |
| `TIMEZONE` | `UTC` | IANA time zone, e.g. `Europe/Berlin` |
| `DIGEST_TIME`, `DIGEST_SIZE` | `08:00`, `5` | when and how many materials |
| `REVIEW_DAY`, `REVIEW_TIME` | `sun`, `11:00` | weekly review schedule |
| `VOICE_REPLIES` | `1` | `0` — text-only replies |
| `GROQ_MODEL`, `WHISPER_MODEL`, `GEMINI_MODEL` | see `.env.example` | model names (providers rename them sometimes) |

## Importing words into Quizlet
1. Tap the grey **For Quizlet** block — the text is copied.
2. On [quizlet.com](https://quizlet.com) (web): **Create → Study set → Import**.
3. Paste. *Between term and definition* → **Custom** → `|`. *Between cards* → **New line**.

## Security
- Owner-only, private-chat-only access.
- Feed links are fetched only from public addresses (no localhost, private networks or cloud metadata), every redirect is re-checked, size and time are limited.
- Web content is passed to the LLM as untrusted data; links and @usernames are stripped from model output to prevent phishing through the bot.
- All output is HTML-escaped, SQL is parameterized, no inbound ports (long polling).
- Sandboxed systemd unit and Docker setup; pinned dependencies checked with `pip-audit` in CI.

Found a vulnerability? See [SECURITY.md](SECURITY.md).

## Privacy
Your messages and the materials you open are sent to Groq, optionally Gemini, and Microsoft (voice). Details: [PRIVACY.md](PRIVACY.md).

## Limitations
- **Personal use.** The bot is single-user. `edge-tts` uses an unofficial endpoint of Microsoft Edge's read-aloud service — fine for personal use, but replace it with a licensed TTS before offering the bot as a service.
- Paywalled articles are discussed from their feed description.
- Only the first ~10 minutes of a podcast are transcribed.
- A discussion lives in memory and is lost when the bot restarts.
- Free API tiers have rate limits; add a Gemini key as a fallback.

## Roadmap
- [ ] Multi-user mode
- [ ] YouTube support
- [ ] Grammar lessons from your own textbook
- [ ] Automatic export to flashcard apps

## Contributing
Issues and pull requests are welcome — see [CONTRIBUTING.md](CONTRIBUTING.md).

## License
[GNU AGPL-3.0](LICENSE). You may use, modify and self-host the bot freely. If you run a modified version as a service for other people, you must publish your source code under the same license.

For a commercial license (closed-source use or a hosted service without AGPL obligations), contact the author.

© 2026 Azha00005
