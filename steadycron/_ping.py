"""Ping transport: fire-and-forget HTTP pings, never raise."""
from __future__ import annotations

import logging
import socket
import urllib.error
import urllib.request
from typing import Optional
from urllib.parse import urlencode

_logger = logging.getLogger("steadycron")

_ERROR_MESSAGE_MAX_BYTES = 1024


def send_ping(
    token: str,
    suffix: Optional[str] = None,
    *,
    env: Optional[str] = None,
    run_id: Optional[str] = None,
    message: Optional[str] = None,
    timeout: float = 5.0,
    ping_url_base: str = "https://ping.steadycron.com",
) -> None:
    """Send a single ping. All errors are swallowed — never raises."""
    base = ping_url_base.rstrip("/")
    path = f"/{token}/{suffix}" if suffix else f"/{token}"
    url = base + path

    qs_parts: dict[str, str] = {}
    if env:
        qs_parts["env"] = env
    if run_id:
        qs_parts["run_id"] = run_id
    if qs_parts:
        url += "?" + urlencode(qs_parts)

    body: Optional[bytes] = None
    if message:
        truncated = _truncate_utf8(message, _ERROR_MESSAGE_MAX_BYTES)
        body = truncated.encode("utf-8")

    req = urllib.request.Request(url, data=body or b"", method="POST")
    if body:
        req.add_header("Content-Type", "text/plain; charset=utf-8")

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = resp.status
            if status >= 300:
                _logger.debug("SteadyCron ping to %s returned HTTP %d.", url, status)
    except TimeoutError:
        _logger.warning("SteadyCron ping to %s timed out after %.1fs.", url, timeout)
    except socket.timeout:
        _logger.warning("SteadyCron ping to %s timed out after %.1fs.", url, timeout)
    except urllib.error.URLError as exc:
        _logger.warning("SteadyCron ping to %s failed: %s", url, exc.reason)
    except Exception as exc:  # noqa: BLE001
        _logger.warning("SteadyCron ping to %s failed unexpectedly: %s", url, exc)


def _truncate_utf8(text: str, max_bytes: int) -> str:
    encoded = text.encode("utf-8")
    if len(encoded) <= max_bytes:
        return text
    truncated = encoded[: max_bytes - 3].decode("utf-8", errors="ignore")
    return truncated + "..."
