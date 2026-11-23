"""Spec 027 Task 18: the preflight selection report is pure and prints no rating."""

from __future__ import annotations

import socket

import pytest

import llmxive.preflight as preflight
from llmxive.model_selection.profiles import PROFILES
from llmxive.preflight import selection_report
from tests.helpers.funded import CODING, REASONING, B, snapshot


def test_report_names_backends_allowance_leaderboard_and_top_candidates():
    lines = selection_report(snapshot(dartmouth=(), sources={"catalog": ("unavailable", 0.0)}))
    assert lines[0] == "backends: dartmouth=unavailable huggingface=live local=live"
    assert lines[1] == "funded allowance: $50.00/month, spent $10.00 this month, $5.00 available now (2026-11)"
    assert lines[2] == "leaderboard: live, published 2026-11-22, reasoning 20 models, coding 20 models"
    # at _REPORT_BUDGET: 8000*1e-7 + 4096*4e-7 = 0.0024384
    assert f"top candidate [cheap_structured] reasoning/economy: {B} (huggingface, funded, worst case $0.0024)" in lines
    assert f"top candidate [deep_code] coding/strong: {B} (huggingface, funded, worst case $0.0024)" in lines
    assert sum(line.startswith("top candidate [") for line in lines) == len(PROFILES)


def test_report_says_unavailable_and_none_without_raising():
    lines = selection_report(snapshot(local=False, available_usd=None))
    assert lines[1] == "funded allowance: unavailable"
    assert any(line.startswith("top candidate [deep_review] reasoning/strong: none — ") for line in lines)


def test_report_prints_no_rating():
    lines = selection_report(snapshot())
    lines += selection_report(snapshot(local=False, available_usd=None))
    ratings = {int(r[i]) for table in (REASONING, CODING) for r in table.values() for i in range(3)}
    for line in lines:
        for rating in ratings:
            assert str(rating) not in line, (rating, line)


def test_main_survives_a_snapshot_failure(monkeypatch, capsys):
    monkeypatch.setenv("DARTMOUTH_CHAT_API_KEY", "x" * 8)

    def boom(**_kw):
        raise RuntimeError("no network")

    monkeypatch.setattr(preflight, "runtime_snapshot", boom)
    preflight.main()
    out = capsys.readouterr().out
    assert "[preflight] info: selection report unavailable: RuntimeError" in out


# --------------------------------------------------------------------------- #
# Provider rule: at least one of Dartmouth key / (HF token + bill-to).
# --------------------------------------------------------------------------- #

@pytest.fixture
def clean_env(monkeypatch, tmp_path):
    """No credential anywhere: no env, no credentials file, no macOS Keychain read."""
    for name in ("DARTMOUTH_CHAT_API_KEY", "HF_TOKEN", "LLMXIVE_HF_BILL_TO"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.setenv("APPDATA", str(tmp_path))
    monkeypatch.setattr("sys.platform", "linux")  # load_hf_token skips the Keychain off macOS
    monkeypatch.setattr(preflight, "runtime_snapshot", lambda **_kw: snapshot())


def _run(capsys):
    rc = preflight.main()
    captured = capsys.readouterr()
    return rc, captured.out, captured.err


def test_hf_pair_only_passes_and_prints_report(clean_env, monkeypatch, capsys):
    monkeypatch.setenv("HF_TOKEN", "t" * 8)
    monkeypatch.setenv("LLMXIVE_HF_BILL_TO", "b" * 8)
    rc, out, err = _run(capsys)
    assert rc == 0, err
    assert "[preflight] info: providers: huggingface configured; dartmouth not configured" in out
    assert "[preflight] info: backends: dartmouth=live huggingface=live local=live" in out
    assert out.count("[preflight] info: top candidate [") == len(PROFILES)
    assert "t" * 8 not in out + err and "b" * 8 not in out + err


def test_dartmouth_only_passes_and_says_hf_not_configured(clean_env, monkeypatch, capsys):
    monkeypatch.setenv("DARTMOUTH_CHAT_API_KEY", "k" * 8)
    rc, out, err = _run(capsys)
    assert rc == 0, err
    assert "providers: dartmouth configured; huggingface not configured" in out
    assert "[preflight] info: funded allowance:" in out


def test_no_credential_fails_fast_naming_both_options(clean_env, capsys):
    rc, out, err = _run(capsys)
    assert rc == 1
    assert "DARTMOUTH_CHAT_API_KEY" in err and "HF_TOKEN" in err and "LLMXIVE_HF_BILL_TO" in err
    assert "top candidate" not in out


def test_token_without_bill_to_fails_naming_bill_to(clean_env, monkeypatch, capsys):
    monkeypatch.setenv("HF_TOKEN", "t" * 8)
    rc, _out, err = _run(capsys)
    assert rc == 1
    assert "Hugging Face is missing ['LLMXIVE_HF_BILL_TO']" in err
    assert "t" * 8 not in err


def test_selection_report_attempts_no_network(monkeypatch):
    def refuse(self, *a, **kw):
        raise AssertionError("selection_report attempted a network connection")

    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr(socket, "create_connection", refuse)
    assert selection_report(snapshot())


def test_unsafe_credentials_file_is_reported_when_hf_carries_the_run(clean_env, monkeypatch, capsys, tmp_path):
    """Final review B3: the permission problem on the Dartmouth credentials file must
    appear in the info line even when Hugging Face is configured."""
    from llmxive import credentials as cred_mod

    path = cred_mod.credentials_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('dartmouth_chat_api_key = "placeholder"\n')
    path.chmod(0o644)
    monkeypatch.setenv("HF_TOKEN", "t" * 8)
    monkeypatch.setenv("LLMXIVE_HF_BILL_TO", "b" * 8)
    rc, out, err = _run(capsys)
    assert rc == 0, err
    line = next(ln for ln in out.splitlines() if "providers: huggingface configured" in ln)
    problem = cred_mod.check_permissions().reason
    assert problem and problem in line
    assert "placeholder" not in out + err
