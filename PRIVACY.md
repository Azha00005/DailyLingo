# Privacy

This bot is **self-hosted**: whoever runs it is responsible for the data it processes.

## What the bot stores (in its local SQLite database)
- Materials from the digest: title, link, description, extracted text or podcast transcript, generated summaries.
- Your mistakes from discussions (the wrong fragment, the correction, the explanation) for the weekly review.

It does **not** store voice recordings, chat history after a discussion ends, or vocabulary lists.

## What is sent to third parties
| Service | What | Why |
|---|---|---|
| Telegram | all bot messages | delivery |
| Groq | your voice messages, your replies, material texts | speech recognition and LLM |
| Google Gemini (optional) | the same texts, if Groq is unavailable | fallback LLM |
| Microsoft (edge-tts) | the bot's reply texts | voice replies |
| Websites from your feeds | ordinary web requests | downloading materials |

Check each provider's terms: free tiers may allow the provider to use your data to improve their models.

## Deleting data
Stop the bot and delete the database file (`english_bot.db`, or `data/` in Docker).

## Running a public instance
If you let other people use your instance, you must publish your own privacy policy (Telegram requires one for bots), get users' consent, follow the data-protection law that applies to you (e.g. GDPR in the EU), and give users a way to delete their data.
