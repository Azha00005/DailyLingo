# Contributing

Thanks for helping! Bug reports, ideas and pull requests are welcome.

## Development setup
```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
ruff check .
pytest
```
Tests do not need real API keys or network access.

## Pull requests
- One change per pull request, with a short description of what and why.
- Keep the bot free-tier friendly: avoid new paid services as hard requirements.
- Never commit `.env`, tokens, API keys, databases or personal data.
- Interface strings go to `locales.py` (add both `en` and `ru`).
- Text from the internet is untrusted: wrap it with `ai.material()` before sending it to an LLM and pass model output through `ai.sanitize()` before showing it.
- Fetch URLs only through `net.fetch()`.

## License of contributions
By submitting a contribution you confirm that you wrote it (or have the right to submit it) and agree that:
1. it is licensed under the project license (GNU AGPL-3.0), and
2. you grant the project maintainer a perpetual, worldwide, non-exclusive, royalty-free right to also license your contribution under other terms, including commercial licenses.

This keeps it possible to offer a commercial license alongside the open-source one.
