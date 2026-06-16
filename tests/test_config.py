"""Tests for module-level config and configure()."""
from __future__ import annotations

import os
import steadycron
from steadycron._config import (
    effective_api_key,
    effective_api_url,
    effective_environment,
    effective_ping_url,
)
from steadycron._resolve import clear_cache


def test_defaults():
    steadycron.api_key = None
    assert steadycron.api_url == "https://api.steadycron.com"
    assert steadycron.ping_url == "https://ping.steadycron.com"
    assert steadycron.capture_errors is False
    assert steadycron.ping_timeout == 5.0
    assert steadycron.resolve_cache_ttl == 3600.0
    assert steadycron.monitors == {}


def test_configure_sets_values():
    orig = steadycron.api_key
    try:
        steadycron.configure(api_key="sc_test", environment="staging")
        assert steadycron.api_key == "sc_test"
        assert steadycron.environment == "staging"
    finally:
        steadycron.api_key = orig
        steadycron.environment = None


def test_effective_api_key_uses_env_var():
    old = steadycron.api_key
    steadycron.api_key = None
    os.environ["STEADYCRON_API_KEY"] = "sc_from_env"
    try:
        assert effective_api_key() == "sc_from_env"
    finally:
        del os.environ["STEADYCRON_API_KEY"]
        steadycron.api_key = old


def test_effective_api_key_explicit_beats_env_var():
    old = steadycron.api_key
    steadycron.api_key = "sc_explicit"
    os.environ["STEADYCRON_API_KEY"] = "sc_from_env"
    try:
        assert effective_api_key() == "sc_explicit"
    finally:
        del os.environ["STEADYCRON_API_KEY"]
        steadycron.api_key = old


def test_effective_api_url_uses_env_var():
    old = steadycron.api_url
    steadycron.api_url = ""  # type: ignore[assignment]
    os.environ["STEADYCRON_API_URL"] = "https://custom.api"
    try:
        assert effective_api_url() == "https://custom.api"
    finally:
        del os.environ["STEADYCRON_API_URL"]
        steadycron.api_url = old


def test_effective_ping_url_uses_env_var():
    old = steadycron.ping_url
    steadycron.ping_url = ""  # type: ignore[assignment]
    os.environ["STEADYCRON_PING_URL"] = "https://custom.ping"
    try:
        assert effective_ping_url() == "https://custom.ping"
    finally:
        del os.environ["STEADYCRON_PING_URL"]
        steadycron.ping_url = old


def test_effective_environment_uses_env_var():
    old = steadycron.environment
    steadycron.environment = None
    os.environ["STEADYCRON_ENVIRONMENT"] = "production"
    try:
        assert effective_environment() == "production"
    finally:
        del os.environ["STEADYCRON_ENVIRONMENT"]
        steadycron.environment = old
