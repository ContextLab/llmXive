"""Keep optional HF operations scoped, bounded, and credential-safe."""

import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest

SPEC = importlib.util.spec_from_file_location(
    "hf_pilot", Path(__file__).parents[2] / "scripts/hf/pilot.py"
)
pilot = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(pilot)


def test_environment_secret_precedes_keychain(monkeypatch):
    monkeypatch.setenv("HF_TOKEN", "test-secret")
    monkeypatch.setattr(
        pilot.subprocess, "run", lambda *a, **kw: pytest.fail("unexpected Keychain read")
    )
    assert pilot.token() == "test-secret"


def test_no_plaintext_cache_fallback(monkeypatch):
    monkeypatch.delenv("HF_TOKEN", raising=False)
    monkeypatch.setattr(pilot.sys, "platform", "linux")
    with pytest.raises(RuntimeError, match="repository secret"):
        pilot.token()


def test_cpu_job_is_bounded_and_has_no_secrets(monkeypatch):
    captured = {}

    def record(method, path, **kwargs):
        captured.update(kwargs["json"])
        assert method == "POST" and path == "/api/jobs/contextlab"
        return {"id": "test"}

    monkeypatch.setattr(pilot, "request", record)
    assert pilot.cpu_probe()["id"] == "test"
    assert captured["resourceGroupId"] == pilot.GROUP
    assert captured["timeoutSeconds"] == 120
    assert captured["attempts"] == 1
    assert captured["flavor"] == "cpu-basic"
    assert not {"environment", "secrets", "expose", "ssh"} & captured.keys()


def test_request_error_does_not_disclose_provider_payload(monkeypatch):
    monkeypatch.setattr(pilot, "token", lambda: "never-print-this")
    monkeypatch.setattr(
        pilot.requests,
        "request",
        lambda *a, **kw: SimpleNamespace(ok=False, status_code=403, text="never-print-this"),
    )
    with pytest.raises(RuntimeError) as error:
        pilot.request("GET", "/api/jobs/contextlab/test")
    assert str(error.value) == "HF request failed with HTTP 403"


def test_inference_bills_group_and_limits_output(monkeypatch):
    monkeypatch.setattr(pilot, "token", lambda: "test-secret")

    def post(url, **kw):
        assert url == "https://router.huggingface.co/v1/chat/completions"
        assert kw["headers"]["X-HF-Bill-To"] == pilot.GROUP
        assert kw["json"]["max_tokens"] == 256
        assert kw["timeout"] == 90
        return SimpleNamespace(ok=True, json=lambda: {"choices": [{"message": {"content": '{"hf_pilot": "ok"}'}}]})

    monkeypatch.setattr(pilot.requests, "post", post)
    assert pilot.inference_probe()["content"] == '{"hf_pilot": "ok"}'
