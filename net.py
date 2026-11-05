"""Безопасная загрузка по ссылкам из RSS-лент.

Ссылки в лентах пишут чужие люди, поэтому:
- только http/https и стандартные порты;
- только публичные IP: никаких localhost, внутренней сети и сервиса метаданных облака (169.254.169.254);
- каждый редирект проверяется заново;
- лимит размера (считается уже распакованный ответ — защита от gzip-бомб) и общий лимит времени.
Остаётся теоретический риск DNS rebinding между проверкой и подключением; для личного бота он приемлем.
"""
import ipaddress
import socket
import time
from urllib.parse import urljoin, urlparse

import httpx

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; EnglishLearningBot/1.0)"}
MAX_REDIRECTS = 5


class UnsafeURL(ValueError):
    pass


def check_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise UnsafeURL(f"Недопустимая ссылка: {url[:100]}")
    if parsed.port not in (None, 80, 443):
        raise UnsafeURL(f"Нестандартный порт: {url[:100]}")
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    try:
        infos = socket.getaddrinfo(parsed.hostname, port, proto=socket.IPPROTO_TCP)
    except socket.gaierror as exc:
        raise UnsafeURL(f"Адрес не найден: {parsed.hostname}") from exc
    for info in infos:
        ip = ipaddress.ip_address(info[4][0].split("%")[0])
        if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
            ip = ip.ipv4_mapped
        if not ip.is_global or ip.is_multicast:
            raise UnsafeURL(f"Адрес во внутренней сети: {parsed.hostname}")


def fetch(url: str, max_bytes: int, *, truncate: bool = False,
          deadline: float = 60, timeout: float = 20) -> bytes:
    """Скачивает не больше max_bytes. truncate=True — вернуть начало, иначе ошибка.
    Синхронно: из асинхронного кода вызывать через asyncio.to_thread."""
    started = time.monotonic()
    with httpx.Client(timeout=timeout, follow_redirects=False, headers=HEADERS) as http:
        for _ in range(MAX_REDIRECTS + 1):
            check_url(url)
            with http.stream("GET", url) as resp:
                if resp.is_redirect:
                    location = resp.headers.get("location")
                    if not location:
                        raise UnsafeURL("Редирект без адреса")
                    url = urljoin(url, location)
                    continue
                resp.raise_for_status()
                length = resp.headers.get("content-length", "")
                if not truncate and length.isdigit() and int(length) > max_bytes:
                    raise ValueError(f"Слишком большой ответ: {length} байт")
                buf = bytearray()
                for chunk in resp.iter_bytes():
                    buf.extend(chunk)
                    if len(buf) > max_bytes:
                        if truncate:
                            return bytes(buf[:max_bytes])
                        raise ValueError("Слишком большой ответ")
                    if time.monotonic() - started > deadline:
                        if truncate:
                            return bytes(buf)
                        raise TimeoutError("Загрузка заняла слишком много времени")
                return bytes(buf)
    raise UnsafeURL("Слишком много редиректов")
