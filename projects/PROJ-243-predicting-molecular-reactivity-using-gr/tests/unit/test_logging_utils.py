"""
Unit tests for logging utilities.
"""
import os
import json
import pytest
import tempfile
import shutil
from datetime import datetime
from unittest.mock import patch, MagicMock

# Mock config before importing logging_utils
@pytest.fixture
def mock_config(tmp_path):
    """Create a temporary directory structure for testing."""
    # Create mock config directory structure
    artifacts_dir = tmp_path / "artifacts"
    logs_dir = artifacts_dir / "logs"
    logs_dir.mkdir(parents=True)
    
    # Mock config data
    mock_config_data = {
        "paths": {
            "artifacts": str(artifacts_dir),
            "logs": str(logs_dir),
            "data": str(tmp_path / "data"),
            "code": str(tmp_path / "code")
        }
    }
    
    return mock_config_data

@pytest.fixture
def setup_test_environment(mock_config):
    """Setup test environment with mocked config."""
    with patch('utils.logging_utils.get_config', return_value=mock_config), \
         patch('utils.logging_utils.ensure_directories'):
        yield mock_config

def test_setup_logging_creates_files(setup_test_environment):
    """Test that setup_logging creates necessary log and metrics files."""
    from utils.logging_utils import setup_logging, get_logger, _metrics_file_path
    
    logger = setup_logging()
    assert logger is not None
    assert logger.level == 20  # INFO level
    
    # Check that metrics file was created
    config = setup_test_environment
    metrics_path = os.path.join(config["paths"]["artifacts"], "metrics.json")
    assert os.path.exists(metrics_path)
    
    # Check log directory exists
    log_dir = os.path.join(config["paths"]["artifacts"], "logs")
    assert os.path.exists(log_dir)

def test_log_metric(setup_test_environment):
    """Test that log_metric correctly writes to metrics file."""
    from utils.logging_utils import setup_logging, log_metric, get_metrics
    
    setup_logging()
    
    # Log a metric
    log_metric("test_metric", 42.5, run_id="test_run")
    
    # Check metrics are stored in memory
    metrics = get_metrics()
    assert "test_metric" in metrics
    assert metrics["test_metric"] == 42.5
    
    # Check metrics file was updated
    config = setup_test_environment
    metrics_path = os.path.join(config["paths"]["artifacts"], "metrics.json")
    
    with open(metrics_path, 'r') as f:
        data = json.load(f)
    
    assert "metrics" in data
    assert len(data["metrics"]) > 0
    
    # Find our metric
    test_metrics = [m for m in data["metrics"] if m["name"] == "test_metric"]
    assert len(test_metrics) == 1
    assert test_metrics[0]["value"] == 42.5

def test_flush_metrics(setup_test_environment):
    """Test that flush_metrics persists all metrics."""
    from utils.logging_utils import setup_logging, log_metric, flush_metrics, _metrics
    
    setup_logging()
    
    # Log some metrics
    log_metric("metric1", 100)
    log_metric("metric2", 200)
    
    # Flush
    flush_metrics()
    
    # Check file contains both metrics
    config = setup_test_environment
    metrics_path = os.path.join(config["paths"]["artifacts"], "metrics.json")
    
    with open(metrics_path, 'r') as f:
        data = json.load(f)
    
    metric_names = [m["name"] for m in data["metrics"]]
    assert "metric1" in metric_names
    assert "metric2" in metric_names

def test_get_metrics(setup_test_environment):
    """Test that get_metrics returns current session metrics."""
    from utils.logging_utils import setup_logging, log_metric, get_metrics
    
    setup_logging()
    log_metric("session_metric", 999)
    
    metrics = get_metrics()
    assert "session_metric" in metrics
    assert metrics["session_metric"] == 999

def test_log_execution_summary(setup_test_environment, caplog):
    """Test that log_execution_summary creates summary file."""
    from utils.logging_utils import setup_logging, log_execution_summary
    
    setup_logging()
    
    # Log a summary
    log_execution_summary(
        task_id="T009_TEST",
        success=True,
        duration_seconds=1.23,
        metrics={"accuracy": 0.95}
    )
    
    # Check summary file exists
    config = setup_test_environment
    summary_path = os.path.join(
        config["paths"]["artifacts"], 
        "logs", 
        "execution_summary.json"
    )
    
    assert os.path.exists(summary_path)
    
    with open(summary_path, 'r') as f:
        data = json.load(f)
    
    assert "summaries" in data
    assert len(data["summaries"]) > 0
    
    # Check our summary
    test_summary = data["summaries"][-1]
    assert test_summary["task_id"] == "T009_TEST"
    assert test_summary["success"] is True
    assert abs(test_summary["duration_seconds"] - 1.23) < 0.01

def test_get_logger_raises_if_not_initialized():
    """Test that get_logger raises RuntimeError if not initialized."""
    from utils.logging_utils import get_logger, _logger
    
    # Temporarily set _logger to None
    import utils.logging_utils as utils_module
    original_logger = utils_module._logger
    utils_module._logger = None
    
    try:
        with pytest.raises(RuntimeError, match="Logging not initialized"):
            get_logger()
    finally:
        utils_module._logger = original_logger
