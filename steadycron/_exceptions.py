"""Exceptions raised by the SteadyCron SDK."""
from __future__ import annotations


class MonitorNotFoundError(Exception):
    """Raised when a job key is not found (resolve returned 404).

    This is a developer/configuration error — verify the key matches
    a job in the SteadyCron Dashboard.
    """

    def __init__(self, key: str) -> None:
        self.key = key
        super().__init__(
            f"Job key '{key}' was not found. "
            "Verify the key matches a job in the SteadyCron Dashboard."
        )


class AmbiguousJobKeyError(Exception):
    """Raised when a key matches more than one job in the account (resolve returned 409).

    Keys must be unique within the account for code monitoring to work.
    """

    def __init__(self, key: str) -> None:
        self.key = key
        super().__init__(
            f"Job key '{key}' is ambiguous — it matches more than one job "
            "in the account. Make the key unique in the SteadyCron Dashboard."
        )


class InvalidMonitorKindError(Exception):
    """Raised when the resolved job has kind 'http' rather than 'heartbeat'.

    HTTP jobs are executed server-side and cannot be pinged from user code.
    """

    def __init__(self, key: str, kind: str) -> None:
        self.key = key
        self.kind = kind
        super().__init__(
            f"Job '{key}' has kind '{kind}'. "
            "Only 'heartbeat' jobs can be pinged from code."
        )


class ConfigurationError(Exception):
    """Raised when neither a direct token nor an API key is available for a key."""

    def __init__(self, key: str) -> None:
        self.key = key
        super().__init__(
            f"No ping token or API key is configured for job '{key}'. "
            "Either set steadycron.api_key or add an entry to steadycron.monitors."
        )
