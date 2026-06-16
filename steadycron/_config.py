"""Module-level configuration and the configure() helper."""
from __future__ import annotations

import os
from typing import Optional

# ── Module-level settings ────────────────────────────────────────────────────

api_key: Optional[str] = None
api_url: str = "https://api.steadycron.com"
ping_url: str = "https://ping.steadycron.com"
environment: Optional[str] = None
capture_errors: bool = False
ping_timeout: float = 5.0
resolve_cache_ttl: float = 3600.0
monitors: dict[str, str] = {}  # key → direct ping token (hardened path)


def configure(
    *,
    api_key: Optional[str] = None,
    api_url: Optional[str] = None,
    ping_url: Optional[str] = None,
    environment: Optional[str] = None,
    capture_errors: Optional[bool] = None,
    ping_timeout: Optional[float] = None,
    resolve_cache_ttl: Optional[float] = None,
) -> None:
    """Set one or more configuration values at once."""
    import steadycron as _mod

    if api_key is not None:
        _mod.api_key = api_key
    if api_url is not None:
        _mod.api_url = api_url
    if ping_url is not None:
        _mod.ping_url = ping_url
    if environment is not None:
        _mod.environment = environment
    if capture_errors is not None:
        _mod.capture_errors = capture_errors
    if ping_timeout is not None:
        _mod.ping_timeout = ping_timeout
    if resolve_cache_ttl is not None:
        _mod.resolve_cache_ttl = resolve_cache_ttl


def effective_api_key() -> Optional[str]:
    """Return the configured API key, falling back to STEADYCRON_API_KEY env var."""
    import steadycron as _mod

    return _mod.api_key or os.environ.get("STEADYCRON_API_KEY")


def effective_api_url() -> str:
    import steadycron as _mod

    return _mod.api_url or os.environ.get("STEADYCRON_API_URL") or "https://api.steadycron.com"


def effective_ping_url() -> str:
    import steadycron as _mod

    return _mod.ping_url or os.environ.get("STEADYCRON_PING_URL") or "https://ping.steadycron.com"


def effective_environment() -> Optional[str]:
    import steadycron as _mod

    return _mod.environment or os.environ.get("STEADYCRON_ENVIRONMENT")
