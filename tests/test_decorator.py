"""Tests for @steadycron.job decorator and steadycron.monitor() context manager."""
from __future__ import annotations

import pytest
import steadycron
from tests.conftest import StubServer


def test_job_decorator_sends_start_success(stub: StubServer) -> None:
    stub.add_monitor("dec-job", "dec-tok")

    @steadycron.job("dec-job")
    def my_task() -> str:
        return "done"

    result = my_task()
    assert result == "done"

    paths = [p.split("?")[0] for p, _ in stub.received_pings]
    assert "/dec-tok/start" in paths
    assert "/dec-tok" in paths


def test_job_decorator_sends_fail_and_reraises(stub: StubServer) -> None:
    stub.add_monitor("fail-dec-job", "fail-tok")
    boom = ValueError("kaboom")

    @steadycron.job("fail-dec-job")
    def bad_task() -> None:
        raise boom

    with pytest.raises(ValueError) as exc_info:
        bad_task()

    assert exc_info.value is boom
    paths = [p.split("?")[0] for p, _ in stub.received_pings]
    assert "/fail-tok/start" in paths
    assert "/fail-tok/fail" in paths


def test_job_decorator_preserves_metadata() -> None:
    @steadycron.job("meta-job")
    def documented_task() -> None:
        """I have a docstring."""

    assert documented_task.__name__ == "documented_task"
    assert documented_task.__doc__ == "I have a docstring."


def test_context_manager_sends_start_success(stub: StubServer) -> None:
    stub.add_monitor("cm-job", "cm-tok")

    with steadycron.monitor("cm-job"):
        pass

    paths = [p.split("?")[0] for p, _ in stub.received_pings]
    assert "/cm-tok/start" in paths
    assert "/cm-tok" in paths


def test_context_manager_sends_fail_and_reraises(stub: StubServer) -> None:
    stub.add_monitor("cm-fail-job", "cm-fail-tok")
    boom = RuntimeError("context boom")

    with pytest.raises(RuntimeError) as exc_info:
        with steadycron.monitor("cm-fail-job"):
            raise boom

    assert exc_info.value is boom
    paths = [p.split("?")[0] for p, _ in stub.received_pings]
    assert "/cm-fail-tok/fail" in paths


def test_capture_errors_sends_message_on_fail(stub: StubServer) -> None:
    stub.add_monitor("capture-job", "cap-tok")
    steadycron.capture_errors = True

    @steadycron.job("capture-job")
    def broken() -> None:
        raise ValueError("disk full")

    with pytest.raises(ValueError):
        broken()

    steadycron.capture_errors = False
    bodies = [b for _, b in stub.received_pings]
    assert any("disk full" in b for b in bodies)


def test_monitor_ping_method(stub: StubServer) -> None:
    stub.add_monitor("manual-job", "man-tok")
    m = steadycron.Monitor("manual-job")
    m.ping()  # bare success heartbeat
    paths = [p.split("?")[0] for p, _ in stub.received_pings]
    assert "/man-tok" in paths


def test_monitor_ping_start(stub: StubServer) -> None:
    stub.add_monitor("manual-start-job", "ms-tok")
    m = steadycron.Monitor("manual-start-job")
    m.ping(state="start")
    paths = [p.split("?")[0] for p, _ in stub.received_pings]
    assert "/ms-tok/start" in paths


def test_direct_token_no_api_key(stub: StubServer) -> None:
    steadycron.api_key = None
    steadycron.monitors["dt-key"] = "dt-tok"

    @steadycron.job("dt-key")
    def direct_task() -> str:
        return "ok"

    result = direct_task()
    assert result == "ok"
    del steadycron.monitors["dt-key"]


def test_run_id_sent_on_all_pings(stub: StubServer) -> None:
    stub.add_monitor("runid-job", "runid-tok")

    @steadycron.job("runid-job")
    def task() -> None:
        pass

    task()
    qs_strings = [p for p, _ in stub.received_pings if "runid-tok" in p]
    run_ids = set()
    for qs in qs_strings:
        if "run_id=" in qs:
            rid = qs.split("run_id=")[1].split("&")[0]
            run_ids.add(rid)
    assert len(run_ids) == 1  # same run_id across all pings for this run
