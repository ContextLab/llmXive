"""Backend reachability check: a transient probe blip must not fail the gate.

The CI pre-flight (llmxive.checks.backends) repeatedly sank PR CI when Dartmouth's
list_models endpoint returned a momentary non-JSON blip — a single-shot probe
treated it as a hard outage. The probe now retries with backoff; a transient error
clears, a sustained outage still fails. Offline / deterministic (no real backend).
"""

from __future__ import annotations

import pytest

from llmxive.backends.base import BackendError
from llmxive.checks import backends as chk


class _FlakyBackend:
    """list_models() fails ``fail_times`` times (transient), then returns models."""

    def __init__(self, fail_times: int) -> None:
        self.fail_times = fail_times
        self.calls = 0

    def list_models(self) -> list[str]:
        self.calls += 1
        if self.calls <= self.fail_times:
            raise BackendError("Dartmouth list_models failed: Expecting value: line 2 column 1")
        return ["qwen.qwen3.5-122b", "gpt-oss-120b"]


@pytest.fixture(autouse=True)
def _no_sleep(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(chk.time, "sleep", lambda *_a, **_k: None)


def test_transient_blip_clears_on_retry() -> None:
    be = _FlakyBackend(fail_times=chk._PROBE_ATTEMPTS - 1)  # fails then succeeds on last try
    models, err = chk._probe_models(be)
    assert err is None
    assert models == ["qwen.qwen3.5-122b", "gpt-oss-120b"]
    assert be.calls == chk._PROBE_ATTEMPTS


def test_first_attempt_success_no_retry() -> None:
    be = _FlakyBackend(fail_times=0)
    models, err = chk._probe_models(be)
    assert err is None and models and be.calls == 1


def test_sustained_outage_still_fails_after_attempts() -> None:
    be = _FlakyBackend(fail_times=999)  # never recovers
    models, err = chk._probe_models(be)
    assert models is None
    assert isinstance(err, BackendError)
    assert be.calls == chk._PROBE_ATTEMPTS  # bounded — fails fast, not forever
