"""Tests for ping transport: fire-and-forget, never raises."""
from __future__ import annotations

import socket
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from steadycron._ping import send_ping
from tests.conftest import StubServer


def test_ping_success_no_suffix(stub: StubServer) -> None:
    stub.add_monitor("ping-job", "ping-tok")
    send_ping("ping-tok", None, timeout=2.0, ping_url_base=stub.url)
    assert any(p == "/ping-tok" for p, _ in stub.received_pings)


def test_ping_start_suffix(stub: StubServer) -> None:
    send_ping("tok", "start", timeout=2.0, ping_url_base=stub.url)
    assert any(p == "/tok/start" for p, _ in stub.received_pings)


def test_ping_fail_suffix(stub: StubServer) -> None:
    send_ping("tok", "fail", timeout=2.0, ping_url_base=stub.url)
    assert any(p == "/tok/fail" for p, _ in stub.received_pings)


def test_ping_500_does_not_raise(stub: StubServer) -> None:
    stub.ping_status = 500
    # Should not raise.
    send_ping("tok", None, timeout=2.0, ping_url_base=stub.url)


def test_ping_refused_connection_does_not_raise() -> None:
    # Use a port that is definitely not listening.
    send_ping("tok", None, timeout=1.0, ping_url_base="http://127.0.0.1:19999")


def test_ping_timeout_does_not_raise() -> None:
    """A ping to a server that hangs must time out without raising."""

    class HangHandler(BaseHTTPRequestHandler):
        def log_message(self, *args: object) -> None:
            pass

        def do_POST(self) -> None:  # noqa: N802
            # Hang indefinitely.
            import time
            time.sleep(60)

    server = HTTPServer(("127.0.0.1", 0), HangHandler)
    _, port = server.server_address
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        send_ping("tok", None, timeout=0.1, ping_url_base=f"http://127.0.0.1:{port}")
    finally:
        server.shutdown()


def test_ping_sends_env_as_query_param(stub: StubServer) -> None:
    send_ping("tok", None, env="production", timeout=2.0, ping_url_base=stub.url)
    paths = [p for p, _ in stub.received_pings]
    assert any("env=production" in p for p in paths)


def test_ping_sends_message_as_body(stub: StubServer) -> None:
    send_ping("tok", "fail", message="disk full", timeout=2.0, ping_url_base=stub.url)
    bodies = [b for _, b in stub.received_pings]
    assert any("disk full" in b for b in bodies)
