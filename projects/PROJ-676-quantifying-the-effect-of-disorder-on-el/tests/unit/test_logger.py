"""
Unit tests for the NumericalLogger class.
"""
import json
import os
import tempfile
from pathlib import Path

from code.logger import NumericalLogger, get_logger


def test_log_residual():
    """Test that log_residual writes correct JSON lines."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = os.path.join(tmpdir, "residuals.json")
        logger = NumericalLogger(output_path=log_path)

        # Log a residual
        logger.log_residual(
            norm=1e-6,
            flag=True,
            task="eigh",
            L=100,
            W=1.0,
            realization_index=5
        )

        # Verify file contents
        assert os.path.exists(log_path)
        with open(log_path, 'r') as f:
            lines = f.readlines()

        assert len(lines) == 1
        entry = json.loads(lines[0])

        assert entry["task"] == "eigh"
        assert entry["residual_norm"] == 1e-6
        assert entry["converged"] is True
        assert entry["L"] == 100
        assert entry["W"] == 1.0
        assert entry["realization_index"] == 5
        assert "timestamp" in entry


def test_log_convergence():
    """Test that log_convergence writes correct JSON lines."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = os.path.join(tmpdir, "residuals.json")
        logger = NumericalLogger(output_path=log_path)

        # Log a convergence metric
        metric = {
            "task": "eigsh",
            "metric_name": "relative_change",
            "value": 1e-7,
            "threshold": 1e-5,
            "converged": True,
            "iteration": 50
        }
        logger.log_convergence(metric)

        # Verify file contents
        assert os.path.exists(log_path)
        with open(log_path, 'r') as f:
            lines = f.readlines()

        assert len(lines) == 1
        entry = json.loads(lines[0])

        assert entry["task"] == "eigsh"
        assert entry["metric_name"] == "relative_change"
        assert entry["value"] == 1e-7
        assert entry["threshold"] == 1e-5
        assert entry["converged"] is True
        assert entry["iteration"] == 50
        assert "timestamp" in entry


def test_multiple_entries():
    """Test that multiple entries are appended correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = os.path.join(tmpdir, "residuals.json")
        logger = NumericalLogger(output_path=log_path)

        logger.log_residual(norm=1e-6, flag=True)
        logger.log_residual(norm=1e-4, flag=False)
        logger.log_convergence({"metric_name": "test", "value": 0.5})

        with open(log_path, 'r') as f:
            lines = f.readlines()

        assert len(lines) == 3


def test_clear_log():
    """Test that clear_log truncates the file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = os.path.join(tmpdir, "residuals.json")
        logger = NumericalLogger(output_path=log_path)

        logger.log_residual(norm=1e-6, flag=True)
        assert os.path.exists(log_path)

        logger.clear_log()

        with open(log_path, 'r') as f:
            content = f.read()

        assert content == ""


def test_get_logger_factory():
    """Test the get_logger factory function."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = os.path.join(tmpdir, "residuals.json")
        logger = get_logger(output_path=log_path)

        assert isinstance(logger, NumericalLogger)
        logger.log_residual(norm=1e-6, flag=True)

        with open(log_path, 'r') as f:
            lines = f.readlines()

        assert len(lines) == 1