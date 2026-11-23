"""
Unit tests for convergence_reporter.py.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest

from code.modeling.convergence_reporter import (
    load_valid_participants,
    load_convergence_logs,
    calculate_convergence_rate,
    verify_threshold,
    generate_convergence_report,
    ConvergenceReportError
)
from code.utils.io import IOLoadError, save_json


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


def test_load_valid_participants_list(temp_dir):
    """Test loading valid participants from a JSON list."""
    valid_file = Path(temp_dir) / "valid_participants.json"
    participants = ["sub-001", "sub-002", "sub-003"]
    save_json(participants, str(valid_file))

    result = load_valid_participants(str(valid_file))
    assert result == participants


def test_load_valid_participants_dict(temp_dir):
    """Test loading valid participants from a JSON dict."""
    valid_file = Path(temp_dir) / "valid_participants.json"
    data = {"participant_ids": ["sub-001", "sub-002"], "count": 2}
    save_json(data, str(valid_file))

    result = load_valid_participants(str(valid_file))
    assert result == ["sub-001", "sub-002"]


def test_load_valid_participants_file_not_found(temp_dir):
    """Test handling of missing valid participants file."""
    valid_file = Path(temp_dir) / "nonexistent.json"
    # Should return empty list, not raise
    result = load_valid_participants(str(valid_file))
    assert result == []


def test_load_convergence_logs(temp_dir):
    """Test loading convergence logs from a directory."""
    logs_dir = Path(temp_dir) / "convergence_logs"
    logs_dir.mkdir()

    # Create valid log files
    logs = {
        "sub-001": {"converged": True, "r_hat_max": 1.01, "ess_min": 200},
        "sub-002": {"converged": False, "r_hat_max": 1.5, "ess_min": 50},
        "sub-003": {"converged": True, "r_hat_max": 1.02, "ess_min": 300}
    }

    for pid, data in logs.items():
        save_json(data, str(logs_dir / f"{pid}.json"))

    result = load_convergence_logs(str(logs_dir))
    assert len(result) == 3
    assert result["sub-001"]["converged"] is True
    assert result["sub-002"]["converged"] is False


def test_load_convergence_logs_missing_dir(temp_dir):
    """Test handling of missing logs directory."""
    logs_dir = Path(temp_dir) / "nonexistent"
    with pytest.raises(IOLoadError):
        load_convergence_logs(str(logs_dir))


def test_calculate_convergence_rate():
    """Test convergence rate calculation."""
    convergence_data = {
        "sub-001": {"converged": True},
        "sub-002": {"converged": False},
        "sub-003": {"converged": True},
        "sub-004": {"converged": True}
    }
    valid_participants = ["sub-001", "sub-002", "sub-003", "sub-004"]

    rate, converged, total = calculate_convergence_rate(convergence_data, valid_participants)

    assert rate == 0.75  # 3/4
    assert converged == 3
    assert total == 4


def test_calculate_convergence_rate_missing_logs():
    """Test calculation when some participants lack logs."""
    convergence_data = {
        "sub-001": {"converged": True},
        "sub-003": {"converged": True}
    }
    valid_participants = ["sub-001", "sub-002", "sub-003"]

    rate, converged, total = calculate_convergence_rate(convergence_data, valid_participants)

    assert rate == 2/3  # sub-002 missing, counts as non-converged? No, logic checks presence
    # Current logic: only counts if in data AND converged. Missing = not counted as converged.
    # So 2 converged out of 3 total.
    assert converged == 2
    assert total == 3


def test_verify_threshold_pass():
    """Test threshold verification when passing."""
    assert verify_threshold(0.91) is True
    assert verify_threshold(0.90) is True
    assert verify_threshold(1.0) is True


def test_verify_threshold_fail():
    """Test threshold verification when failing."""
    assert verify_threshold(0.89) is False
    assert verify_threshold(0.5) is False


def test_generate_convergence_report_pass(temp_dir):
    """Test report generation when threshold is met."""
    convergence_data = {
        "sub-001": {"converged": True, "r_hat_max": 1.01, "ess_min": 200},
        "sub-002": {"converged": True, "r_hat_max": 1.02, "ess_min": 250},
        "sub-003": {"converged": True, "r_hat_max": 1.01, "ess_min": 300}
    }
    valid_participants = ["sub-001", "sub-002", "sub-003"]
    output_path = Path(temp_dir) / "report.json"

    report = generate_convergence_report(convergence_data, valid_participants, str(output_path))

    assert report["convergence_rate"] == 1.0
    assert report["threshold_passed"] is True
    assert output_path.exists()


def test_generate_convergence_report_fail(temp_dir):
    """Test report generation when threshold is NOT met (raises error)."""
    convergence_data = {
        "sub-001": {"converged": True, "r_hat_max": 1.01, "ess_min": 200},
        "sub-002": {"converged": False, "r_hat_max": 1.5, "ess_min": 50},
        "sub-003": {"converged": False, "r_hat_max": 1.6, "ess_min": 40}
    }
    valid_participants = ["sub-001", "sub-002", "sub-003"]
    output_path = Path(temp_dir) / "report.json"

    with pytest.raises(ConvergenceReportError):
        generate_convergence_report(convergence_data, valid_participants, str(output_path))

def test_generate_convergence_report_empty_valid(temp_dir):
    """Test report generation with no valid participants."""
    convergence_data = {}
    valid_participants = []
    output_path = Path(temp_dir) / "report.json"

    # Should return 0 rate, not raise
    report = generate_convergence_report(convergence_data, valid_participants, str(output_path))
    assert report["convergence_rate"] == 0.0
    assert report["total_valid_count"] == 0