import pytest
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.utils.logging_config import (
    _api_metrics_registry,
    reset_metrics,
    log_api_call,
    get_api_logger
)
from src.utils.api_metrics import (
    aggregate_and_report,
    check_thresholds,
    calculate_success_ratio
)

@pytest.fixture(autouse=True)
def reset_metrics_before_test():
    """Ensure metrics are clean before each test."""
    reset_metrics()
    yield
    reset_metrics()

def test_log_api_call_success():
    """Test logging a successful API call updates the registry."""
    logger = get_api_logger("test_success")
    log_api_call(logger, "NpmClient", "/top", "SUCCESS")

    key = "NpmClient:/top"
    assert key in _api_metrics_registry
    assert _api_metrics_registry[key]["success"] == 1
    assert _api_metrics_registry[key]["failure"] == 0

def test_log_api_call_failure():
    """Test logging a failed API call updates the registry."""
    logger = get_api_logger("test_failure")
    log_api_call(logger, "GithubClient", "/commits", "FAILURE")

    key = "GithubClient:/commits"
    assert key in _api_metrics_registry
    assert _api_metrics_registry[key]["failure"] == 1
    assert _api_metrics_registry[key]["success"] == 0

def test_calculate_success_ratio():
    """Test calculation of success ratio."""
    # Setup
    log_api_call(get_api_logger("ratio_test"), "Svc", "Ep", "SUCCESS")
    log_api_call(get_api_logger("ratio_test"), "Svc", "Ep", "SUCCESS")
    log_api_call(get_api_logger("ratio_test"), "Svc", "Ep", "FAILURE")

    ratio = calculate_success_ratio("Svc", "Ep")
    assert ratio == pytest.approx(0.6666, rel=0.01)

def test_aggregate_and_report():
    """Test that aggregate_and_report produces correct summary."""
    # Setup data
    log_api_call(get_api_logger("agg_test"), "A", "1", "SUCCESS")
    log_api_call(get_api_logger("agg_test"), "A", "1", "FAILURE")
    log_api_call(get_api_logger("agg_test"), "B", "2", "SUCCESS")
    log_api_call(get_api_logger("agg_test"), "B", "2", "SUCCESS")
    log_api_call(get_api_logger("agg_test"), "B", "2", "SUCCESS")

    report = aggregate_and_report()

    assert report["total_calls"] == 5
    assert report["total_success"] == 4
    assert report["total_failure"] == 1
    assert report["overall_success_ratio"] == pytest.approx(0.8)

    assert "A:1" in report["endpoints"]
    assert report["endpoints"]["A:1"]["success_ratio"] == pytest.approx(0.5)
    assert report["endpoints"]["B:2"]["success_ratio"] == pytest.approx(1.0)

def test_aggregate_and_report_writes_file():
    """Test that aggregate_and_report writes to the specified path."""
    log_api_call(get_api_logger("file_test"), "X", "Y", "SUCCESS")

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        aggregate_and_report(output_path=tmp_path)
        assert os.path.exists(tmp_path)
        with open(tmp_path, 'r') as f:
            data = json.load(f)
        assert "generated_at" in data
        assert data["total_success"] == 1
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

def test_check_thresholds_pass():
    """Test check_thresholds returns True when ratio is high enough."""
    log_api_call(get_api_logger("thresh_test"), "T", "1", "SUCCESS")
    log_api_call(get_api_logger("thresh_test"), "T", "1", "SUCCESS")
    log_api_call(get_api_logger("thresh_test"), "T", "1", "SUCCESS")

    # 100% success, threshold 0.95
    assert check_thresholds(0.95) is True

def test_check_thresholds_fail():
    """Test check_thresholds returns False when ratio is too low."""
    log_api_call(get_api_logger("thresh_fail"), "F", "1", "SUCCESS")
    log_api_call(get_api_logger("thresh_fail"), "F", "1", "FAILURE")
    log_api_call(get_api_logger("thresh_fail"), "F", "1", "FAILURE")
    log_api_call(get_api_logger("thresh_fail"), "F", "1", "FAILURE")

    # 25% success, threshold 0.95
    assert check_thresholds(0.95) is False

def test_empty_metrics():
    """Test behavior when no metrics have been recorded."""
    reset_metrics()
    report = aggregate_and_report()
    assert report["total_calls"] == 0
    assert report["overall_success_ratio"] == 0.0