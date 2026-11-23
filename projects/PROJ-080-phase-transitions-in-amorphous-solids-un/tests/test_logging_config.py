import pytest
import logging
import os
import tempfile
from pathlib import Path
import shutil

# Import the module under test
from code.logging_config import (
    configure_logging,
    get_logger,
    log_indeterminate_warning,
    log_multi_yield_event,
    log_data_fetch_failure,
    log_synthetic_fallback_active,
    log_numerical_instability,
    log_checksum_mismatch,
    log_particle_limit_exceeded,
    INDENTED_WARNING_PREFIX
)

@pytest.fixture
def temp_log_dir():
    """Create a temporary directory for log files."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)

def test_configure_logging_creates_file(temp_log_dir):
    """Test that configure_logging creates the log file and sets up handlers."""
    log_file_name = "test_pipeline.log"
    logger = configure_logging(
        log_level=logging.INFO,
        log_file=log_file_name,
        log_dir=temp_log_dir
    )
    
    assert logger is not None
    log_path = Path(temp_log_dir) / log_file_name
    assert log_path.exists()
    
    # Verify handlers
    assert len(logger.handlers) == 2  # File and Console

def test_log_indeterminate_warning(temp_log_dir):
    """Test that indeterminate warnings are logged with correct prefix."""
    log_file_name = "test_indeterminate.log"
    configure_logging(
        log_level=logging.WARNING,
        log_file=log_file_name,
        log_dir=temp_log_dir
    )
    
    # Log a warning
    log_indeterminate_warning(
        "No sharp stress peak found",
        trajectory_id="traj_001",
        reason="Low signal-to-noise"
    )
    
    log_path = Path(temp_log_dir) / log_file_name
    with open(log_path, 'r') as f:
        content = f.read()
    
    assert INDENTED_WARNING_PREFIX in content
    assert "No sharp stress peak found" in content
    assert "trajectory_id=traj_001" in content
    assert "reason=Low signal-to-noise" in content

def test_log_multi_yield_event(temp_log_dir):
    """Test logging of multiple yielding events."""
    log_file_name = "test_multi_yield.log"
    configure_logging(
        log_level=logging.WARNING,
        log_file=log_file_name,
        log_dir=temp_log_dir
    )
    
    log_multi_yield_event(
        trajectory_id="traj_002",
        yield_timestamps=[100, 250, 400]
    )
    
    log_path = Path(temp_log_dir) / log_file_name
    with open(log_path, 'r') as f:
        content = f.read()
    
    assert INDENTED_WARNING_PREFIX in content
    assert "Multiple yielding events detected" in content
    assert "traj_002" in content
    assert "[100, 250, 400]" in content

def test_log_data_fetch_failure_with_fallback(temp_log_dir):
    """Test logging of data fetch failure with synthetic fallback."""
    log_file_name = "test_fetch_fail.log"
    configure_logging(
        log_level=logging.WARNING,
        log_file=log_file_name,
        log_dir=temp_log_dir
    )
    
    try:
        raise ConnectionError("Network unreachable")
    except ConnectionError as e:
        log_data_fetch_failure(
            dataset_id="materials-science/test",
            error=e,
            fallback_to_synthetic=True
        )
    
    log_path = Path(temp_log_dir) / log_file_name
    with open(log_path, 'r') as f:
        content = f.read()
    
    assert INDENTED_WARNING_PREFIX in content
    assert "Failed to fetch real data" in content
    assert "SYNTHETIC FALLBACK ACTIVE" in content

def test_log_synthetic_fallback_active(temp_log_dir):
    """Test explicit logging of synthetic fallback activation."""
    log_file_name = "test_fallback.log"
    configure_logging(
        log_level=logging.WARNING,
        log_file=log_file_name,
        log_dir=temp_log_dir
    )
    
    log_synthetic_fallback_active(
        source_path="/data/raw/synthetic_trajectory_001.h5"
    )
    
    log_path = Path(temp_log_dir) / log_file_name
    with open(log_path, 'r') as f:
        content = f.read()
    
    assert INDENTED_WARNING_PREFIX in content
    assert "SYNTHETIC FALLBACK ACTIVE" in content
    assert "/data/raw/synthetic_trajectory_001.h5" in content

def test_log_numerical_instability(temp_log_dir):
    """Test logging of numerical instability."""
    log_file_name = "test_numerical.log"
    configure_logging(
        log_level=logging.WARNING,
        log_file=log_file_name,
        log_dir=temp_log_dir
    )
    
    log_numerical_instability(
        component="D2_min",
        value_type="strain",
        stats={"nan_count": 5, "inf_count": 0}
    )
    
    log_path = Path(temp_log_dir) / log_file_name
    with open(log_path, 'r') as f:
        content = f.read()
    
    assert INDENTED_WARNING_PREFIX in content
    assert "Numerical instability detected" in content
    assert "D2_min" in content
    assert "nan_count: 5" in content

def test_log_checksum_mismatch(temp_log_dir):
    """Test logging of checksum mismatch."""
    log_file_name = "test_checksum.log"
    configure_logging(
        log_level=logging.CRITICAL,
        log_file=log_file_name,
        log_dir=temp_log_dir
    )
    
    log_checksum_mismatch(
        artifact_path="/data/processed/precursor_metrics.csv",
        expected="abc123...",
        actual="def456..."
    )
    
    log_path = Path(temp_log_dir) / log_file_name
    with open(log_path, 'r') as f:
        content = f.read()
    
    assert INDENTED_WARNING_PREFIX in content
    assert "Checksum validation FAILED" in content
    assert "abc123..." in content
    assert "def456..." in content

def test_log_particle_limit_exceeded(temp_log_dir):
    """Test logging of particle limit exceeded."""
    log_file_name = "test_limit.log"
    configure_logging(
        log_level=logging.ERROR,
        log_file=log_file_name,
        log_dir=temp_log_dir
    )
    
    log_particle_limit_exceeded(count=150000, limit=100000)
    
    log_path = Path(temp_log_dir) / log_file_name
    with open(log_path, 'r') as f:
        content = f.read()
    
    assert INDENTED_WARNING_PREFIX in content
    assert "Particle count (150000) exceeds limit (100000)" in content
    assert "FR-006" in content