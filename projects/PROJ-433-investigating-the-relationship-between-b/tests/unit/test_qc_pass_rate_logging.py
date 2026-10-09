"""Tests for the QC pass‑rate logging script."""

import logging
from pathlib import Path

import pytest

# Import the functions directly for isolated testing
from log_qc_pass_rate import (
    _parse_qc_log,
    _log_qc_pass_rate,
)

@pytest.fixture
def tmp_logs(tmp_path):
    """Create temporary preprocess and analysis logs."""
    preprocess_log = tmp_path / "data" / "preprocess_log.txt"
    analysis_log = tmp_path / "data" / "analysis_log.txt"

    # Ensure parent directories exist
    preprocess_log.parent.mkdir(parents=True, exist_ok=True)
    analysis_log.parent.mkdir(parents=True, exist_ok=True)

    # Write a deterministic set of QC entries
    # 3 passes, 2 fails → 60% pass rate
    lines = [
        "Subject 01 – QC PASS – FD=0.32",
        "Subject 02 – QC FAIL – FD=0.62",
        "Subject 03 – QC PASS – FD=0.28",
        "Subject 04 – QC FAIL – FD=0.71",
        "Subject 05 – QC PASS – FD=0.45",
    ]
    preprocess_log.write_text("\n".join(lines), encoding="utf-8")

    return {
        "preprocess_log": preprocess_log,
        "analysis_log": analysis_log,
    }

def test_parse_qc_log(tmp_logs):
    passed, total = _parse_qc_log(tmp_logs["preprocess_log"])
    assert passed == 3
    assert total == 5

def test_log_qc_pass_rate(tmp_logs, caplog):
    # Set up a logger that writes to the temporary analysis log file
    logger = logging.getLogger("test_logger")
    logger.setLevel(logging.INFO)

    # Attach a FileHandler pointing at the temporary analysis log
    handler = logging.FileHandler(tmp_logs["analysis_log"], mode="a", encoding="utf-8")
    formatter = logging.Formatter("%(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Capture log output via caplog as well
    with caplog.at_level(logging.INFO, logger=logger.name):
        _log_qc_pass_rate(passed=3, total=5, logger=logger)

    # Verify the message appears in both the captured log and the file
    expected_message = "SC-001: 60.0% subjects passed fMRIPrep QC"
    assert expected_message in caplog.text

    # Flush and read the file content
    handler.flush()
    file_contents = tmp_logs["analysis_log"].read_text(encoding="utf-8")
    assert expected_message in file_contents

    # Clean up handler
    logger.removeHandler(handler)
    handler.close()