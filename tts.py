"""Озвучка ответов бота бесплатными голосами Microsoft Edge."""
import edge_tts

from config import TTS_RATE, TTS_VOICE


async def synthesize(text: str) -> bytes:
    """Возвращает MP3 — Telegram принимает его как голосовое сообщение."""
    communicate = edge_tts.Communicate(text, TTS_VOICE, rate=TTS_RATE)
    audio = bytearray()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio.extend(chunk["data"])
    return bytes(audio)
