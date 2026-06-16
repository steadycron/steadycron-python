"""Token resolution: resolve a monitor key to its ping token via the API."""
from __future__ import annotations

import json
import logging
import threading
import time
import urllib.error
import urllib.request
from typing import Optional
from urllib.parse import urlencode

from ._exceptions import (
    AmbiguousJobKeyError,
    ConfigurationError,
    InvalidMonitorKindError,
    MonitorNotFoundError,
)

_logger = logging.getLogger("steadycron")

# Cache: key → (token, expires_at_unix)
_cache: dict[str, tuple[str, float]] = {}
_cache_lock = threading.Lock()


def _cache_get(key: str) -> Optional[str]:
    with _cache_lock:
        entry = _cache.get(key)
        if entry is not None and entry[1] > time.monotonic():
            return entry[0]
    return None


def _cache_set(key: str, token: str, ttl: float) -> None:
    with _cache_lock:
        _cache[key] = (token, time.monotonic() + ttl)


def clear_cache() -> None:
    """Clear the entire resolution cache (useful in tests)."""
    with _cache_lock:
        _cache.clear()


def resolve_token(key: str) -> str:
    """Return the ping token for *key*, using cache or the resolve endpoint.

    Raises:
        ConfigurationError: if neither a direct token nor an API key is available.
        MonitorNotFoundError: if the key is not found (404).
        AmbiguousJobKeyError: if the key matches multiple monitors (409).
        InvalidMonitorKindError: if the resolved monitor is not a heartbeat.
    """
    import steadycron as _mod

    # 1. Direct token map (hardened path).
    direct = _mod.monitors.get(key)
    if direct:
        return direct

    # 2. Cache.
    cached = _cache_get(key)
    if cached is not None:
        return cached

    # 3. Resolve via API key.
    api_key = _mod.api_key or __import__("os").environ.get("STEADYCRON_API_KEY")
    if not api_key:
        raise ConfigurationError(key)

    api_url = (_mod.api_url or __import__("os").environ.get("STEADYCRON_API_URL") or "https://api.steadycron.com").rstrip("/")
    params = urlencode({"key": key})
    url = f"{api_url}/api/monitors/resolve?{params}"

    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {api_key}"})
    try:
        with urllib.request.urlopen(req) as resp:
            body = json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            raise MonitorNotFoundError(key) from exc
        if exc.code == 409:
            raise AmbiguousJobKeyError(key) from exc
        raise RuntimeError(f"Resolve returned HTTP {exc.code} for key '{key}'.") from exc

    kind = body.get("kind", "")
    if kind != "heartbeat":
        raise InvalidMonitorKindError(key, kind)

    ping_token: Optional[str] = body.get("ping_token")
    if not ping_token:
        raise RuntimeError(f"Resolve response missing ping_token for key '{key}'.")

    ttl = _mod.resolve_cache_ttl
    _cache_set(key, ping_token, ttl)
    return ping_token
