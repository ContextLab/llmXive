"""
Unit tests for the Failure Handler module (T024).

Tests verify that:
1. Convergence failures are logged correctly.
2. Realizations are excluded from analysis.
3. The exclusion list is accurate.
"""

import os
import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Adjust import path for testing
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from gap_filling.failure_handler import (
    ensure_failure_log_dir,
    log_convergence_failure,
    record_excluded_realization,
    handle_convergence_failure,
    get_excluded_realization_ids,
    is_realization_excluded
)

@pytest.fixture
def temp_failure_dir():
    """Create a temporary directory for failure logs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Patch the global path
        with patch('gap_filling.failure_handler.FAILURE_LOG_DIR', Path(tmpdir)):
            yield Path(tmpdir)

def test_ensure_failure_log_dir_creates_directory(temp_failure_dir):
    """Test that the failure log directory is created if missing."""
    # The fixture sets up the path, but we call the function to ensure logic works
    result = ensure_failure_log_dir()
    assert result.exists()
    assert result.is_dir()

def test_log_convergence_failure(temp_failure_dir):
    """Test that a failure is logged to the correct JSON file."""
    realization_id = "test_001"
    algo_name = "harmonic_interp"
    error_msg = "Convergence not reached"
    
    log_path = log_convergence_failure(
        realization_id=realization_id,
        algo_name=algo_name,
        gap_fraction=0.1,
        gap_morphology="random",
        error_message=error_msg
    )
    
    assert os.path.exists(log_path)
    
    with open(log_path, 'r') as f:
        data = json.load(f)
    
    assert len(data) == 1
    assert data[0]["realization_id"] == realization_id
    assert data[0]["algorithm"] == algo_name
    assert data[0]["error"] == error_msg
    assert data[0]["gap_config"]["fraction"] == 0.1
    assert data[0]["gap_config"]["morphology"] == "random"

def test_record_excluded_realization(temp_failure_dir):
    """Test that a realization is recorded as excluded."""
    realization_id = "test_002"
    
    record_excluded_realization(realization_id, reason="convergence_failure")
    
    exclusion_log = temp_failure_dir / "excluded_realizations.json"
    assert exclusion_log.exists()
    
    with open(exclusion_log, 'r') as f:
        data = json.load(f)
    
    assert len(data) == 1
    assert data[0]["realization_id"] == realization_id
    assert data[0]["reason"] == "convergence_failure"

def test_handle_convergence_failure_integration(temp_failure_dir):
    """Test the full handler flow: log + exclude."""
    realization_id = "test_003"
    algo_name = "wiener_filter"
    exc = Exception("Divergence detected")
    
    result = handle_convergence_failure(
        realization_id=realization_id,
        algo_name=algo_name,
        gap_fraction=0.2,
        gap_morphology="clustered",
        exception=exc
    )
    
    assert result is True
    
    # Verify exclusion
    assert is_realization_excluded(realization_id)
    
    # Verify log
    log_path = temp_failure_dir / "convergence_failures.json"
    with open(log_path, 'r') as f:
        data = json.load(f)
    
    assert any(item["realization_id"] == realization_id for item in data)

def test_get_excluded_realization_ids(temp_failure_dir):
    """Test retrieving the set of excluded IDs."""
    # Record a few
    record_excluded_realization("id_a")
    record_excluded_realization("id_b")
    
    excluded = get_excluded_realization_ids()
    
    assert "id_a" in excluded
    assert "id_b" in excluded
    assert len(excluded) == 2

def test_is_realization_excluded_negative(temp_failure_dir):
    """Test that a non-excluded ID returns False."""
    assert not is_realization_excluded("non_existent_id")