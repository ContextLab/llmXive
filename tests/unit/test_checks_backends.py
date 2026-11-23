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


# --- final review A6: the check passes when at least one provider is usable -------------

def _env(monkeypatch, tmp_path, *, dartmouth: bool, hf: bool) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))  # no credentials file
    monkeypatch.delenv("DARTMOUTH_CHAT_API_KEY", raising=False)
    monkeypatch.delenv("HF_TOKEN", raising=False)
    monkeypatch.delenv("LLMXIVE_HF_BILL_TO", raising=False)
    monkeypatch.setattr("llmxive.credentials.sys.platform", "linux")  # no Keychain lookup
    if dartmouth:
        monkeypatch.setenv("DARTMOUTH_CHAT_API_KEY", "placeholder-not-a-key")
    if hf:
        monkeypatch.setenv("HF_TOKEN", "hf_placeholder")
        monkeypatch.setenv("LLMXIVE_HF_BILL_TO", "placeholder-group")


def _hf_at(monkeypatch, srv) -> None:
    from llmxive.backends.huggingface import HuggingFaceBackend

    real = chk.backend_router.make_backend
    monkeypatch.setattr(
        chk.backend_router, "make_backend",
        lambda name: HuggingFaceBackend(base_url=srv.base_url) if name == "huggingface" else real(name),
    )


def test_dartmouth_unconfigured_but_huggingface_usable_passes(monkeypatch, tmp_path, capsys):
    from tests.helpers.replay_server import ReplayServer

    _env(monkeypatch, tmp_path, dartmouth=False, hf=True)
    with ReplayServer({("GET", "/models"): [(200, {"data": [{"id": "acme/alpha"}]})] * 5}) as srv:
        _hf_at(monkeypatch, srv)
        assert chk.main() == 0
    out = capsys.readouterr()
    assert "huggingface OK" in out.out
    assert "dartmouth" in out.err and "FAIL" not in out.err


def test_no_usable_provider_fails(monkeypatch, tmp_path, capsys):
    from tests.helpers.replay_server import ReplayServer

    _env(monkeypatch, tmp_path, dartmouth=False, hf=True)
    with ReplayServer({("GET", "/models"): [(503, {"error": "down"})] * 5}) as srv:
        _hf_at(monkeypatch, srv)
        assert chk.main() == 1
    err = capsys.readouterr().err
    assert "FAIL" in err and "dartmouth" in err and "huggingface" in err


def test_nothing_configured_fails(monkeypatch, tmp_path, capsys):
    _env(monkeypatch, tmp_path, dartmouth=False, hf=False)
    assert chk.main() == 1
    assert "FAIL" in capsys.readouterr().err


def test_dartmouth_down_but_huggingface_usable_passes(monkeypatch, tmp_path, capsys):
    """Dartmouth configured but its catalog answers 503 on every probe (an outage):
    the real-call gate must still pass so the Hugging Face lane can run."""
    from llmxive.backends import dartmouth
    from tests.helpers.replay_server import ReplayServer

    _env(monkeypatch, tmp_path, dartmouth=True, hf=True)
    with ReplayServer({("GET", "/models"): [(503, {"error": "down"})] * 5}) as down, \
         ReplayServer({("GET", "/models"): [(200, {"data": [{"id": "acme/alpha"}]})] * 5}) as up:
        monkeypatch.setattr(dartmouth, "_cloud_models_url", lambda: down.base_url + "/models")
        _hf_at(monkeypatch, up)
        assert chk.main() == 0
        assert len(down.requests) == chk._PROBE_ATTEMPTS  # Dartmouth really was probed
    out = capsys.readouterr()
    assert "huggingface OK" in out.out
    assert "dartmouth" in out.err and "FAIL" not in out.err
