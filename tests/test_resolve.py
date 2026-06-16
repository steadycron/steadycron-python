"""Tests for the resolver and TTL cache."""
from __future__ import annotations

import time

import pytest
import steadycron
from steadycron._exceptions import (
    AmbiguousJobKeyError,
    ConfigurationError,
    InvalidMonitorKindError,
    MonitorNotFoundError,
)
from steadycron._resolve import clear_cache, resolve_token
from tests.conftest import StubServer


def test_resolve_returns_token(stub: StubServer) -> None:
    stub.add_monitor("my-job", "tok123")
    assert resolve_token("my-job") == "tok123"


def test_resolve_404_raises_not_found(stub: StubServer) -> None:
    with pytest.raises(MonitorNotFoundError) as exc_info:
        resolve_token("missing-key")
    assert exc_info.value.key == "missing-key"


def test_resolve_409_raises_ambiguous(stub: StubServer) -> None:
    stub.resolve_responses["dup-key"] = (409, {"error": "ambiguous_key"})
    with pytest.raises(AmbiguousJobKeyError) as exc_info:
        resolve_token("dup-key")
    assert exc_info.value.key == "dup-key"


def test_resolve_http_kind_raises_invalid_kind(stub: StubServer) -> None:
    stub.add_monitor("http-job", "tok999", kind="http")
    with pytest.raises(InvalidMonitorKindError) as exc_info:
        resolve_token("http-job")
    assert exc_info.value.key == "http-job"
    assert exc_info.value.kind == "http"


def test_resolve_no_api_key_raises_configuration_error(stub: StubServer) -> None:
    steadycron.api_key = None
    with pytest.raises(ConfigurationError):
        resolve_token("any-key")


def test_token_is_cached(stub: StubServer) -> None:
    stub.add_monitor("cached-job", "cached-tok")
    resolve_token("cached-job")

    # Remove stub so a second resolve call would fail.
    stub.resolve_responses.clear()

    # Should still return cached token.
    assert resolve_token("cached-job") == "cached-tok"


def test_cache_expires(stub: StubServer) -> None:
    stub.add_monitor("expiry-job", "tok-v1")
    steadycron.resolve_cache_ttl = 0.05  # 50 ms

    resolve_token("expiry-job")
    time.sleep(0.1)

    # Update the stub to return a new token.
    stub.add_monitor("expiry-job", "tok-v2")
    token = resolve_token("expiry-job")
    assert token == "tok-v2"
    steadycron.resolve_cache_ttl = 3600.0


def test_direct_token_skips_resolution(stub: StubServer) -> None:
    steadycron.monitors["direct-key"] = "direct-tok"
    # No resolve stub — would fail if the endpoint were called.
    token = resolve_token("direct-key")
    assert token == "direct-tok"
    del steadycron.monitors["direct-key"]
