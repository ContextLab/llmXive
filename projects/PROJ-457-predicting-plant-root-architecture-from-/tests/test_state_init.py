"""Tests for T005: project state initialisation and ISRIC deviation log."""

import json
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATE_PATH = PROJECT_ROOT / "artifacts" / "state.json"
FALLBACK_LOG_PATH = PROJECT_ROOT / "artifacts" / "logs" / "fallback.log"
REQUIRED_MESSAGE = (
    "ISRIC source not verified – proceeding without soil interpolation"
)


def test_state_file_has_isric_flag_false():
    assert STATE_PATH.exists(), f"Missing state file: {STATE_PATH}"
    with open(STATE_PATH, "r", encoding="utf-8") as f:
        state = json.load(f)
    assert state.get("is_isric_verified") is False


def test_fallback_log_contains_required_message():
    assert FALLBACK_LOG_PATH.exists(), f"Missing log: {FALLBACK_LOG_PATH}"
    with open(FALLBACK_LOG_PATH, "r", encoding="utf-8") as f:
        text = f.read()
    assert REQUIRED_MESSAGE in text


def test_init_state_script_runs_cleanly():
    result = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "code" / "init_state.py")],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
    )
    assert result.returncode == 0, result.stderr
    # Idempotency: message appears exactly once after re-running.
    with open(FALLBACK_LOG_PATH, "r", encoding="utf-8") as f:
        text = f.read()
    assert text.count(REQUIRED_MESSAGE) == 1