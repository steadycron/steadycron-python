"""SteadyCron code-monitoring SDK for Python.

Quickstart::

    import steadycron

    steadycron.api_key = "sc_ro_..."  # read-only key, or set STEADYCRON_API_KEY env var

    @steadycron.job("nightly-db-backup")
    def backup():
        ...   # start on entry, success on return, fail (+re-raise) on exception

"""
from __future__ import annotations

from typing import Optional

# ── Module-level configuration (set directly or via configure()) ──────────────
api_key: Optional[str] = None
api_url: str = "https://api.steadycron.com"
ping_url: str = "https://ping.steadycron.com"
environment: Optional[str] = None
capture_errors: bool = False
ping_timeout: float = 5.0
resolve_cache_ttl: float = 3600.0
monitors: dict[str, str] = {}  # key → direct ping token (hardened path)

# ── Public API ────────────────────────────────────────────────────────────────
from ._config import configure
from ._exceptions import (
    AmbiguousJobKeyError,
    ConfigurationError,
    InvalidMonitorKindError,
    MonitorNotFoundError,
)
from ._monitor import Monitor, job, monitor
from ._resolve import clear_cache

__all__ = [
    # Config
    "api_key",
    "api_url",
    "ping_url",
    "environment",
    "capture_errors",
    "ping_timeout",
    "resolve_cache_ttl",
    "monitors",
    "configure",
    # Core API
    "Monitor",
    "job",
    "monitor",
    # Exceptions
    "MonitorNotFoundError",
    "AmbiguousJobKeyError",
    "InvalidMonitorKindError",
    "ConfigurationError",
    # Utils
    "clear_cache",
]
