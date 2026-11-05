FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY *.py feeds.txt ./

# Run as an unprivileged user; the database lives in the /app/data volume
RUN useradd --create-home --uid 10001 bot && mkdir -p /app/data && chown bot:bot /app/data
USER bot
ENV DB_PATH=/app/data/english_bot.db

CMD ["python", "bot.py"]
