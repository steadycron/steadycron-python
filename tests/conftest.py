"""Shared test fixtures: a lightweight stub HTTP server using only stdlib."""
from __future__ import annotations

import json
import socket
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Generator
from urllib.parse import parse_qs, urlparse

import pytest
import steadycron
from steadycron._resolve import clear_cache


class StubHandler(BaseHTTPRequestHandler):
    """Minimal HTTP handler that records requests and returns configured responses."""

    def log_message(self, *args: object) -> None:
        pass  # silence access log during tests

    def do_GET(self) -> None:  # noqa: N802
        server: StubServer = self.server  # type: ignore[assignment]
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)
        key = qs.get("key", [""])[0]

        if parsed.path == "/api/monitors/resolve":
            response = server.resolve_responses.get(key, (404, {"error": "monitor_not_found"}))
            status, body = response
            self._send_json(status, body)
        else:
            self._send_json(404, {"error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802
        server: StubServer = self.server  # type: ignore[assignment]
        # Store the full path including query string so tests can assert on env/run_id params.
        full_path = self.path
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else ""
        server.received_pings.append((full_path, body))
        self._send_json(server.ping_status, {})

    def _send_json(self, status: int, body: object) -> None:
        data = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


class StubServer(HTTPServer):
    """Extended HTTPServer that stores state for assertions."""

    def __init__(self) -> None:
        super().__init__(("127.0.0.1", 0), StubHandler)
        self.resolve_responses: dict[str, tuple[int, object]] = {}
        self.received_pings: list[tuple[str, str]] = []
        self.ping_status: int = 200

    @property
    def url(self) -> str:
        host, port = self.server_address
        return f"http://{host}:{port}"

    def add_monitor(self, key: str, token: str, kind: str = "heartbeat") -> None:
        self.resolve_responses[key] = (
            200,
            {"key": key, "job_id": "00000000-0000-0000-0000-000000000001", "kind": kind, "ping_token": token},
        )


@pytest.fixture()
def stub() -> Generator[StubServer, None, None]:
    server = StubServer()
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    # Point steadycron at the stub server.
    original = {
        "api_key": steadycron.api_key,
        "api_url": steadycron.api_url,
        "ping_url": steadycron.ping_url,
        "environment": steadycron.environment,
        "capture_errors": steadycron.capture_errors,
        "ping_timeout": steadycron.ping_timeout,
        "resolve_cache_ttl": steadycron.resolve_cache_ttl,
        "monitors": dict(steadycron.monitors),
    }

    steadycron.api_key = "sc_test_ro"
    steadycron.api_url = server.url
    steadycron.ping_url = server.url
    steadycron.environment = None
    steadycron.capture_errors = False
    steadycron.ping_timeout = 2.0
    steadycron.resolve_cache_ttl = 3600.0
    steadycron.monitors = {}
    clear_cache()

    yield server

    server.shutdown()
    steadycron.api_key = original["api_key"]
    steadycron.api_url = original["api_url"]
    steadycron.ping_url = original["ping_url"]
    steadycron.environment = original["environment"]  # type: ignore[assignment]
    steadycron.capture_errors = original["capture_errors"]  # type: ignore[assignment]
    steadycron.ping_timeout = original["ping_timeout"]  # type: ignore[assignment]
    steadycron.resolve_cache_ttl = original["resolve_cache_ttl"]  # type: ignore[assignment]
    steadycron.monitors = original["monitors"]
    clear_cache()
