"""
Unit tests for ``code.utils.verify_logging``.
The tests create a temporary pipeline log with the required JSON‑line
structure and ensure that ``verify_log`` succeeds when all stages are
present and raises ``RuntimeError`` when any stage is missing.
"""

import json
from pathlib import Path

import pytest

# Import the verification function from the module we just created.
from code.utils.verify_logging import verify_log, EXPECTED_STAGES


@pytest.fixture
def temp_log(tmp_path: Path) -> Path:
    """
    Create a temporary pipeline log file containing one entry for each
    expected stage.  Each line is a JSON object with at least a ``stage``
    key; additional fields are irrelevant for verification.
    """
    log_path = tmp_path / "pipeline.log"
    with log_path.open("w", encoding="utf-8") as f:
        for stage in EXPECTED_STAGES:
            entry = {"stage": stage, "message": f"{stage} completed"}
            f.write(json.dumps(entry) + "\n")
    return log_path


def test_verify_log_success(temp_log: Path):
    """All expected stages are present → no exception."""
    # The function uses the default path; we pass the temporary path explicitly.
    verify_log(log_path=temp_log, expected_stages=EXPECTED_STAGES)


def test_verify_log_missing_stage(temp_log: Path):
    """Remove one stage from the log → RuntimeError."""
    # Rewrite the log without the last expected stage.
    missing_stage = EXPECTED_STAGES[-1]
    with temp_log.open("w", encoding="utf-8") as f:
        for stage in EXPECTED_STAGES[:-1]:
            entry = {"stage": stage, "message": f"{stage} completed"}
            f.write(json.dumps(entry) + "\n")
    with pytest.raises(RuntimeError) as excinfo:
        verify_log(log_path=temp_log, expected_stages=EXPECTED_STAGES)
    assert missing_stage in str(excinfo.value)


def test_verify_log_empty_file(tmp_path: Path):
    """An empty log file should raise RuntimeError."""
    empty_log = tmp_path / "empty.log"
    empty_log.touch()
    with pytest.raises(RuntimeError) as excinfo:
        verify_log(log_path=empty_log, expected_stages=EXPECTED_STAGES)
    assert "empty" in str(excinfo.value).lower()


def test_verify_log_nonexistent_path(tmp_path: Path):
    """A non‑existent log path should raise RuntimeError."""
    missing_path = tmp_path / "does_not_exist.log"
    with pytest.raises(RuntimeError) as excinfo:
        verify_log(log_path=missing_path, expected_stages=EXPECTED_STAGES)
    assert "not found" in str(excinfo.value).lower()