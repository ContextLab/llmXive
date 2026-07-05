"""Unit tests for the logging infrastructure (T007)."""
import logging
import os
import tempfile
from pathlib import Path
import pytest

# Import the module under test
from code.utils.logging import setup_logging, get_logger, log_convergence_failure, log_simulation_progress


@pytest.fixture
def temp_log_dir(tmp_path):
    """Create a temporary directory for log files."""
    log_dir = tmp_path / "data" / "results"
    log_dir.mkdir(parents=True)
    return log_dir


def test_setup_logging_creates_file(temp_log_dir):
    """Test that setup_logging creates the log file."""
    log_file = temp_log_dir / "test_simulation.log"
    
    # Reset global state for clean test
    import code.utils.logging as logging_module
    logging_module._logger = None

    logger = setup_logging(
        level=logging.INFO,
        log_file=log_file,
        console=False
    )

    assert logger is not None
    assert log_file.exists()

def test_get_logger_returns_instance(temp_log_dir):
    """Test that get_logger returns a valid logger."""
    log_file = temp_log_dir / "test_simulation_2.log"
    
    import code.utils.logging as logging_module
    logging_module._logger = None

    setup_logging(log_file=log_file, console=False)
    
    logger = get_logger("test_submodule")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "llmXive.test_submodule"

def test_log_convergence_failure(temp_log_dir):
    """Test that convergence failures are logged correctly."""
    log_file = temp_log_dir / "test_convergence.log"
    
    import code.utils.logging as logging_module
    logging_module._logger = None

    setup_logging(log_file=log_file, console=False)
    
    log_convergence_failure("REML", "study_123", "Iteration limit reached")
    
    # Verify file content
    content = log_file.read_text()
    assert "CONVERGENCE FAILURE" in content
    assert "REML" in content
    assert "study_123" in content
    assert "Iteration limit reached" in content

def test_log_simulation_progress(temp_log_dir):
    """Test that simulation progress is logged correctly."""
    log_file = temp_log_dir / "test_progress.log"
    
    import code.utils.logging as logging_module
    logging_module._logger = None

    setup_logging(log_file=log_file, console=False)
    
    log_simulation_progress(current=10, total=100, level=0.5, replicate=5)
    
    content = log_file.read_text()
    assert "Progress" in content
    assert "10/100" in content
    assert "τ²=0.5" in content
    assert "Replicate 5" in content