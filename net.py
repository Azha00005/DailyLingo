"""Safe downloading of links from RSS feeds.

Links in feeds are written by strangers, so:
- only http/https and standard ports;
- only public IPs: no localhost, internal network or cloud metadata service (169.254.169.254);
- every redirect is re-checked;
- a size limit (counted on the decompressed response — protects against gzip bombs) and an overall time limit.
A theoretical DNS rebinding risk remains between the check and the connection; it is acceptable for a personal bot.
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
        raise UnsafeURL(f"Invalid link: {url[:100]}")
    if parsed.port not in (None, 80, 443):
        raise UnsafeURL(f"Non-standard port: {url[:100]}")
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    try:
        infos = socket.getaddrinfo(parsed.hostname, port, proto=socket.IPPROTO_TCP)
    except socket.gaierror as exc:
        raise UnsafeURL(f"Host not found: {parsed.hostname}") from exc
    for info in infos:
        ip = ipaddress.ip_address(info[4][0].split("%")[0])
        if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
            ip = ip.ipv4_mapped
        if not ip.is_global or ip.is_multicast:
            raise UnsafeURL(f"Host in an internal network: {parsed.hostname}")


def fetch(url: str, max_bytes: int, *, truncate: bool = False,
          deadline: float = 60, timeout: float = 20) -> bytes:
    """Downloads at most max_bytes. truncate=True returns the beginning, otherwise raises an error.
    Synchronous: from async code call via asyncio.to_thread."""
    started = time.monotonic()
    with httpx.Client(timeout=timeout, follow_redirects=False, headers=HEADERS) as http:
        for _ in range(MAX_REDIRECTS + 1):
            check_url(url)
            with http.stream("GET", url) as resp:
                if resp.is_redirect:
                    location = resp.headers.get("location")
                    if not location:
                        raise UnsafeURL("Redirect without a location")
                    url = urljoin(url, location)
                    continue
                resp.raise_for_status()
                length = resp.headers.get("content-length", "")
                if not truncate and length.isdigit() and int(length) > max_bytes:
                    raise ValueError(f"Response too large: {length} bytes")
                buf = bytearray()
                for chunk in resp.iter_bytes():
                    buf.extend(chunk)
                    if len(buf) > max_bytes:
                        if truncate:
                            return bytes(buf[:max_bytes])
                        raise ValueError("Response too large")
                    if time.monotonic() - started > deadline:
                        if truncate:
                            return bytes(buf)
                        raise TimeoutError("Download took too long")
                return bytes(buf)
    raise UnsafeURL("Too many redirects")
