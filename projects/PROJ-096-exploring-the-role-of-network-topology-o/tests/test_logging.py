"""
Tests for the logging infrastructure (T008).
"""
import os
import sys
import json
import tempfile
import logging
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from utils.logging_utils import (
    init_logging,
    get_logger,
    log_simulation_params,
    log_warning,
    log_error,
    log_critical,
    log_metric,
    DEFAULT_LOG_DIR,
    DEFAULT_LOG_FILE
)

def test_init_logging_creates_file():
    """Test that init_logging creates the log file in the correct directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_dir = Path(tmpdir) / "processed"
        log_file = "test_simulation.log"
        
        # Initialize logging to temp directory
        init_logging(log_dir=log_dir, log_file=log_file, level=logging.INFO)
        
        # Verify file exists
        log_path = log_dir / log_file
        assert log_path.exists(), f"Log file not created at {log_path}"

def test_logger_retrieval():
    """Test that get_logger returns a valid logger."""
    logger = get_logger("test_module")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "kuramoto_research"

def test_log_simulation_params():
    """Test that simulation parameters are logged correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_dir = Path(tmpdir) / "processed"
        log_file = "params_test.log"
        
        # Re-initialize to clean state
        import utils.logging_utils
        utils.logging_utils._initialized = False
        utils.logging_utils._logger = None
        utils.logging_utils._handler = None
        
        init_logging(log_dir=log_dir, log_file=log_file, level=logging.INFO)
        
        params = {
            "rewiring_prob": 0.5,
            "N": 500,
            "k": 2,
            "seed": 42
        }
        
        log_simulation_params(params, experiment_id="exp_001")
        
        # Read log and verify content
        log_path = log_dir / log_file
        with open(log_path, 'r') as f:
            content = f.read()
        
        assert "SIMULATION_PARAMS" in content
        assert "exp_001" in content
        assert "0.5" in content  # rewiring_prob

def test_log_warning():
    """Test warning logging."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_dir = Path(tmpdir) / "processed"
        log_file = "warning_test.log"
        
        import utils.logging_utils
        utils.logging_utils._initialized = False
        utils.logging_utils._logger = None
        
        init_logging(log_dir=log_dir, log_file=log_file, level=logging.WARNING)
        
        log_warning("Test warning message", category="TOPOLOGY")
        
        log_path = log_dir / log_file
        with open(log_path, 'r') as f:
            content = f.read()
        
        assert "WARNING" in content
        assert "[TOPOLOGY]" in content
        assert "Test warning message" in content

def test_log_error():
    """Test error logging."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_dir = Path(tmpdir) / "processed"
        log_file = "error_test.log"
        
        import utils.logging_utils
        utils.logging_utils._initialized = False
        utils.logging_utils._logger = None
        
        init_logging(log_dir=log_dir, log_file=log_file, level=logging.ERROR)
        
        log_error("Test error message", category="CONVERGENCE")
        
        log_path = log_dir / log_file
        with open(log_path, 'r') as f:
            content = f.read()
        
        assert "ERROR" in content
        assert "[CONVERGENCE]" in content
        assert "Test error message" in content

def test_log_metric():
    """Test metric logging."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_dir = Path(tmpdir) / "processed"
        log_file = "metric_test.log"
        
        import utils.logging_utils
        utils.logging_utils._initialized = False
        utils.logging_utils._logger = None
        
        init_logging(log_dir=log_dir, log_file=log_file, level=logging.INFO)
        
        log_metric("critical_coupling", 2.345, tags={"topology": "ws"})
        
        log_path = log_dir / log_file
        with open(log_path, 'r') as f:
            content = f.read()
        
        assert "METRIC" in content
        assert "2.345" in content
        assert "ws" in content

def test_log_critical():
    """Test critical logging."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_dir = Path(tmpdir) / "processed"
        log_file = "critical_test.log"
        
        import utils.logging_utils
        utils.logging_utils._initialized = False
        utils.logging_utils._logger = None
        
        init_logging(log_dir=log_dir, log_file=log_file, level=logging.CRITICAL)
        
        log_critical("Critical failure in simulation", category="STABILITY")
        
        log_path = log_dir / log_file
        with open(log_path, 'r') as f:
            content = f.read()
        
        assert "CRITICAL" in content
        assert "[STABILITY]" in content
        assert "Critical failure" in content
