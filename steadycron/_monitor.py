"""Monitor class, @job decorator, and monitor() context manager."""
from __future__ import annotations

import functools
import uuid
from contextlib import contextmanager
from typing import Any, Callable, Generator, Optional, TypeVar

from ._ping import send_ping
from ._resolve import resolve_token

F = TypeVar("F", bound=Callable[..., Any])


class Monitor:
    """Represents a named SteadyCron monitor for manual ping control."""

    def __init__(self, key: str) -> None:
        self.key = key

    def ping(
        self,
        state: str = "success",
        message: Optional[str] = None,
    ) -> None:
        """Send a ping.

        Args:
            state: One of ``"start"``, ``"success"`` (default), or ``"fail"``.
            message: Optional error message; sent only when ``state="fail"``
                     (or always if explicitly provided).
        """
        import steadycron as _mod

        token = resolve_token(self.key)
        suffix = state if state != "success" else None
        ping_url = (_mod.ping_url or __import__("os").environ.get("STEADYCRON_PING_URL") or "https://ping.steadycron.com")
        env = _mod.environment or __import__("os").environ.get("STEADYCRON_ENVIRONMENT")
        send_ping(
            token,
            suffix,
            env=env,
            message=message if (state == "fail" or message is not None) else None,
            timeout=_mod.ping_timeout,
            ping_url_base=ping_url,
        )


def _run_tracked(key: str, fn: Callable[..., Any], args: Any, kwargs: Any) -> Any:
    """Core tracking logic shared by the decorator and context manager."""
    import steadycron as _mod

    token = resolve_token(key)
    run_id = uuid.uuid4().hex
    ping_url = (_mod.ping_url or __import__("os").environ.get("STEADYCRON_PING_URL") or "https://ping.steadycron.com")
    env = _mod.environment or __import__("os").environ.get("STEADYCRON_ENVIRONMENT")
    timeout = _mod.ping_timeout

    send_ping(token, "start", env=env, run_id=run_id, timeout=timeout, ping_url_base=ping_url)
    try:
        result = fn(*args, **kwargs)
        send_ping(token, None, env=env, run_id=run_id, timeout=timeout, ping_url_base=ping_url)
        return result
    except Exception:
        msg: Optional[str] = None
        if _mod.capture_errors:
            import sys
            exc = sys.exc_info()[1]
            msg = str(exc) if exc is not None else None
        send_ping(token, "fail", env=env, run_id=run_id, message=msg, timeout=timeout, ping_url_base=ping_url)
        raise


def job(key: str) -> Callable[[F], F]:
    """Decorator: wrap a function with start/success/fail pings.

    Usage::

        @steadycron.job("nightly-db-backup")
        def backup():
            ...
    """

    def decorator(fn: F) -> F:
        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return _run_tracked(key, fn, args, kwargs)

        return wrapper  # type: ignore[return-value]

    return decorator


@contextmanager
def monitor(key: str) -> Generator[Monitor, None, None]:
    """Context manager: wrap a block with start/success/fail pings.

    Usage::

        with steadycron.monitor("nightly-db-backup"):
            run_backup()
    """
    import steadycron as _mod

    token = resolve_token(key)
    run_id = uuid.uuid4().hex
    ping_url = (_mod.ping_url or __import__("os").environ.get("STEADYCRON_PING_URL") or "https://ping.steadycron.com")
    env = _mod.environment or __import__("os").environ.get("STEADYCRON_ENVIRONMENT")
    timeout = _mod.ping_timeout

    send_ping(token, "start", env=env, run_id=run_id, timeout=timeout, ping_url_base=ping_url)
    try:
        yield Monitor(key)
        send_ping(token, None, env=env, run_id=run_id, timeout=timeout, ping_url_base=ping_url)
    except Exception:
        msg2: Optional[str] = None
        if _mod.capture_errors:
            import sys
            exc2 = sys.exc_info()[1]
            msg2 = str(exc2) if exc2 is not None else None
        send_ping(token, "fail", env=env, run_id=run_id, message=msg2, timeout=timeout, ping_url_base=ping_url)
        raise
