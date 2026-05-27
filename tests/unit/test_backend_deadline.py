"""Unit tests for backends.base.invoke_with_deadline.

Regression guard for the ~54-min CI hang: the Dartmouth backend wrapped its
LLM call in `with ThreadPoolExecutor(...) as ex: ex.submit(...).result(180)`.
When the 180s deadline fired and raised, the `with` block's __exit__ called
shutdown(wait=True), which BLOCKED waiting for the still-hung worker thread —
so the deadline never actually freed the caller. These tests use a real
sleeping callable (no mocks) and assert the caller regains control promptly
once the deadline passes, instead of waiting for the slow call to finish.
"""

from __future__ import annotations

import threading
import time

import pytest

from llmxive.backends.base import TransientBackendError, invoke_with_deadline


def test_returns_value_on_fast_success() -> None:
    assert invoke_with_deadline(lambda: 42, timeout=5.0, description="fast") == 42


def test_reraises_callable_exception() -> None:
    """If the wrapped call raises, that exception propagates to the caller
    (so each backend's own transient/permanent classifier can handle it)."""

    class _Boom(RuntimeError):
        pass

    def _raise() -> None:
        raise _Boom("kaboom")

    with pytest.raises(_Boom, match="kaboom"):
        invoke_with_deadline(_raise, timeout=5.0, description="boom")


def test_deadline_fires_and_returns_promptly() -> None:
    """A call that sleeps far past the deadline must (a) raise
    TransientBackendError and (b) hand control back at ~the deadline, NOT
    after the slow call finishes. The old ThreadPoolExecutor form blocked
    on shutdown(wait=True) until the 30s sleep completed — this asserts we
    don't."""
    started = time.monotonic()
    with pytest.raises(TransientBackendError, match="hung past 1s deadline"):
        invoke_with_deadline(lambda: time.sleep(30), timeout=1.0, description="slow model")
    elapsed = time.monotonic() - started
    # Must return right after the 1s deadline — well before the 30s sleep.
    assert elapsed < 5.0, f"caller was blocked {elapsed:.1f}s past the deadline"


def test_abandoned_worker_is_daemon_and_does_not_block_exit() -> None:
    """The abandoned worker must be a daemon thread (so it never blocks
    interpreter exit) and the slow call keeps running in the background
    after we've already raised — i.e. we truly abandoned it rather than
    cancelling/joining it."""
    release = threading.Event()
    ran_to_completion = threading.Event()

    def _slow() -> None:
        release.wait(timeout=10.0)
        ran_to_completion.set()

    with pytest.raises(TransientBackendError):
        invoke_with_deadline(_slow, timeout=0.3, description="daemon check")

    # The worker is the only non-main llmxive-backend thread; confirm daemon.
    backend_threads = [
        t for t in threading.enumerate() if t.name.startswith("llmxive-backend-")
    ]
    assert backend_threads, "expected the abandoned worker thread to still exist"
    assert all(t.daemon for t in backend_threads), "abandoned worker must be daemon"

    # Let it finish so we don't leak it past the test.
    release.set()
    assert ran_to_completion.wait(timeout=5.0), "abandoned worker never completed"
