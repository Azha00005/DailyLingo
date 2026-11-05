import httpx
import pytest

import net

BLOCKED = [
    "http://127.0.0.1/", "http://localhost/", "http://169.254.169.254/opc/v2/instance/",
    "http://10.0.0.5/", "http://192.168.1.1/", "http://[::1]/", "http://[::ffff:127.0.0.1]/",
    "http://0.0.0.0/", "file:///etc/passwd", "javascript:alert(1)", "ftp://example.com/",
    "http://example.com:8080/",
]


@pytest.mark.parametrize("url", BLOCKED)
def test_blocks_unsafe_urls(url):
    with pytest.raises(net.UnsafeURL):
        net.check_url(url)


def _mock_client(monkeypatch, handler):
    original = httpx.Client.__init__

    def init(self, *args, **kwargs):
        kwargs["transport"] = httpx.MockTransport(handler)
        original(self, *args, **kwargs)

    monkeypatch.setattr(httpx.Client, "__init__", init)
    real_check = net.check_url
    monkeypatch.setattr(net, "check_url",
                        lambda url: None if "example.org" in url else real_check(url))


def test_blocks_redirect_to_internal(monkeypatch):
    _mock_client(monkeypatch, lambda r: httpx.Response(302, headers={"location": "http://127.0.0.1/admin"}))
    with pytest.raises(net.UnsafeURL):
        net.fetch("https://example.org/feed", 1000)


def test_size_limit(monkeypatch):
    _mock_client(monkeypatch, lambda r: httpx.Response(200, content=b"x" * 5000))
    with pytest.raises(ValueError):
        net.fetch("https://example.org/big", 1000)
    assert len(net.fetch("https://example.org/big", 1000, truncate=True)) == 1000
