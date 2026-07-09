"""
Unit tests for the logging infrastructure (T009).
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Import the module under test
# We assume this file is run from the project root or PYTHONPATH is set correctly
from code.utils.logger import (
    get_logger,
    log_qc_failure,
    log_convergence_status,
    get_qc_summary,
    get_convergence_summary,
    _get_log_dir
)
from code.utils.config import set_config, reset_config

@pytest.fixture(autouse=True)
def setup_test_config(tmp_path):
    """Set up a temporary config for each test to isolate log files."""
    reset_config()
    # Point logs to a temporary directory
    test_log_dir = tmp_path / "data" / "reports" / "logs"
    set_config({"log_dir": str(test_log_dir)})
    yield test_log_dir
    reset_config()

def test_get_logger_creates_instance():
    """Test that get_logger returns a valid logger instance."""
    logger = get_logger("test_unit_logger")
    assert logger is not None
    assert logger.name == "test_unit_logger"
    # Ensure handlers are added
    assert len(logger.handlers) > 0

def test_get_logger_returns_same_instance():
    """Test that calling get_logger twice returns the same object."""
    logger1 = get_logger("test_singleton_logger")
    logger2 = get_logger("test_singleton_logger")
    assert logger1 is logger2

def test_log_qc_failure_writes_jsonl(setup_test_config):
    """Test that QC failures are written to the correct JSONL file."""
    log_dir = setup_test_config
    qc_file = log_dir / "qc_failures.jsonl"
    
    log_qc_failure(
        participant_id="P001",
        stage="motion_correction",
        reason="FD > 3mm",
        details={"fd_value": 4.5}
    )
    
    assert qc_file.exists(), "QC failure log file should be created."
    
    with open(qc_file, 'r') as f:
        line = f.readline()
        record = json.loads(line)
    
    assert record["participant_id"] == "P001"
    assert record["stage"] == "motion_correction"
    assert record["reason"] == "FD > 3mm"
    assert record["details"]["fd_value"] == 4.5
    assert record["status"] == "failed"

def test_log_convergence_status_writes_jsonl(setup_test_config):
    """Test that convergence logs are written correctly."""
    log_dir = setup_test_config
    conv_file = log_dir / "convergence_log.jsonl"
    
    log_convergence_status(
        participant_id="P002",
        model_name="belief_updater",
        converged=True,
        r_hat=1.01,
        ess=500,
        runtime_seconds=120.5
    )
    
    assert conv_file.exists()
    
    with open(conv_file, 'r') as f:
        line = f.readline()
        record = json.loads(line)
    
    assert record["participant_id"] == "P002"
    assert record["converged"] is True
    assert record["r_hat"] == 1.01
    assert record["runtime_seconds"] == 120.5
    assert record["status"] == "success"

def test_get_qc_summary(setup_test_config):
    """Test the QC summary aggregation."""
    log_qc_failure("P001", "motion", "High FD")
    log_qc_failure("P002", "normalization", "Missing mask")
    log_qc_failure("P001", "smoothing", "Kernel error")
    
    summary = get_qc_summary()
    
    assert summary["total_failures"] == 3
    assert summary["by_stage"]["motion"] == 1
    assert summary["by_stage"]["normalization"] == 1
    assert summary["by_stage"]["smoothing"] == 1
    assert "P001" in summary["participants"]
    assert "P002" in summary["participants"]

def test_get_convergence_summary(setup_test_config):
    """Test the convergence summary aggregation."""
    log_convergence_status("P001", "model", True, r_hat=1.0)
    log_convergence_status("P002", "model", False, r_hat=1.5)
    log_convergence_status("P003", "model", True, r_hat=1.02)
    
    summary = get_convergence_summary()
    
    assert summary["total_models"] == 3
    assert summary["converged"] == 2
    assert summary["rate"] == pytest.approx(2/3)
    assert summary["failed_count"] == 1

def test_get_qc_summary_empty_file(setup_test_config):
    """Test summary when no failures exist."""
    summary = get_qc_summary()
    assert summary["total_failures"] == 0
    assert summary["by_stage"] == {}

def test_get_convergence_summary_empty_file(setup_test_config):
    """Test summary when no convergence logs exist."""
    summary = get_convergence_summary()
    assert summary["total_models"] == 0
    assert summary["rate"] == 0.0