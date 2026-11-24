"""credentials.load_hf_token: env first, then macOS Keychain; never a plaintext cache.

Real subprocess against a real executable written to tmp_path (no mocks).
"""

from llmxive.credentials import load_hf_token


def _fake_security(tmp_path, body):
    p = tmp_path / "security"
    p.write_text("#!/bin/sh\n" + body + "\n")
    p.chmod(0o755)
    return str(p)


def test_env_wins(monkeypatch, tmp_path):
    monkeypatch.setenv("HF_TOKEN", "  hf_env  ")
    assert load_hf_token(platform="darwin", security_bin=_fake_security(tmp_path, "echo hf_kc")) == "hf_env"


def test_keychain_used_on_darwin_when_env_absent(monkeypatch, tmp_path):
    monkeypatch.delenv("HF_TOKEN", raising=False)
    argv = tmp_path / "argv"
    sec = _fake_security(tmp_path, f'echo "$@" > {argv}; echo hf_kc')
    assert load_hf_token(platform="darwin", security_bin=sec) == "hf_kc"
    assert argv.read_text().split() == ["find-generic-password", "-s", "llmxive-huggingface", "-w"]


def test_keychain_miss_and_non_darwin_return_none(monkeypatch, tmp_path):
    monkeypatch.delenv("HF_TOKEN", raising=False)
    assert load_hf_token(platform="darwin", security_bin=_fake_security(tmp_path, "exit 44")) is None
    assert load_hf_token(platform="linux", security_bin=_fake_security(tmp_path, "echo hf_kc")) is None


def test_plaintext_hub_cache_is_never_read(monkeypatch, tmp_path):
    monkeypatch.delenv("HF_TOKEN", raising=False)
    (tmp_path / "token").write_text("hf_cache")
    monkeypatch.setenv("HF_HOME", str(tmp_path))
    monkeypatch.setenv("HUGGING_FACE_HUB_TOKEN", "hf_legacy")
    assert load_hf_token(platform="linux") is None


def test_slow_keychain_times_out_as_no_token(monkeypatch, tmp_path):
    monkeypatch.delenv("HF_TOKEN", raising=False)
    sec = _fake_security(tmp_path, "sleep 5; echo hf_kc")
    assert load_hf_token(platform="darwin", security_bin=sec, timeout_s=0.3) is None
