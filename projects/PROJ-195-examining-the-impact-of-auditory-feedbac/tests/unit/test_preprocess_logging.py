import json
import logging
import tempfile
from pathlib import Path
import pytest

from preprocess import log_preprocessing_deviations, setup_logging

def test_log_preprocessing_deviations_format():
    """
    Test that log_preprocessing_deviations writes valid JSON to the log file.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "test.log"
        logger = setup_logging(log_path)

        deviation = {
            "subject": "sub-01",
            "step": "motion_qc",
            "status": "exceeded",
            "details": "Motion > 2mm"
        }

        log_preprocessing_deviations(logger, deviation)

        # Read the file and validate JSON
        with open(log_path, 'r') as f:
            lines = f.readlines()
            assert len(lines) > 0
            
            # Parse the JSON line
            try:
                log_entry = json.loads(lines[-1])
                assert log_entry["subject"] == "sub-01"
                assert log_entry["step"] == "motion_qc"
                assert log_entry["status"] == "exceeded"
                assert "Deviation" in log_entry["message"]
            except json.JSONDecodeError:
                pytest.fail("Log entry is not valid JSON")

def test_log_preprocessing_deviations_fmriprep_failure():
    """
    Test logging for fMRIPrep failure deviation.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "test.log"
        logger = setup_logging(log_path)

        deviation = {
            "subject": "sub-02",
            "step": "fmriprep_execution",
            "status": "failed",
            "details": "Subprocess error"
        }

        log_preprocessing_deviations(logger, deviation)

        with open(log_path, 'r') as f:
            lines = f.readlines()
            log_entry = json.loads(lines[-1])
            assert log_entry["step"] == "fmriprep_execution"
            assert log_entry["status"] == "failed"