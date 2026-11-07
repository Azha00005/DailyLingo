"""Voices the bot's replies with free Microsoft Edge voices."""
import edge_tts

from config import TTS_RATE, TTS_VOICE


async def synthesize(text: str) -> bytes:
    """Returns MP3 — Telegram accepts it as a voice message."""
    communicate = edge_tts.Communicate(text, TTS_VOICE, rate=TTS_RATE)
    audio = bytearray()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio.extend(chunk["data"])
    return bytes(audio)
