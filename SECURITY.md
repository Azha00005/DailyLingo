# Security policy

## Reporting a vulnerability
Please **do not open a public issue** for security problems.
Report privately via GitHub: **Security → Report a vulnerability** in this repository
(or email: azh.khizr@gmail.com).

Include what is affected, steps to reproduce and the possible impact. You will get a reply within 7 days.

## Supported versions
Only the latest release receives security fixes.

## Hardening checklist for self-hosting
- `chmod 600 .env`; never publish or commit it.
- In @BotFather: `/setjoingroups` → Disable.
- Server firewall: allow only inbound SSH (port 22), ideally from your IP only. The bot needs no inbound ports.
- Enable automatic security updates (`unattended-upgrades` on Ubuntu).
- Run `pip-audit -r requirements.txt` monthly.
- If a token or key leaks: revoke the bot token in @BotFather (`/revoke`), recreate Groq/Gemini keys, update `.env`, restart.
