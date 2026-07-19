"""
Tests for state_manager module.

These tests verify the metadata logging functionality for numerically
unresolved realizations as required by task T011.
"""

import json
import os
import pytest
from pathlib import Path
import tempfile
import shutil

# We need to temporarily modify the module to use temp directories
# for testing without affecting the actual project state
import sys
import importlib

@pytest.fixture(autouse=True)
def setup_test_environment(tmp_path):
    """Set up a temporary directory structure for testing."""
    # Store original paths
    original_metadata_path = "data/raw/metadata.json"
    original_state_dir = "state"
    original_unresolved_log = "state/unresolved_realizations.json"
    
    # Create temp directories
    temp_data_raw = tmp_path / "data" / "raw"
    temp_data_raw.mkdir(parents=True, exist_ok=True)
    temp_state = tmp_path / "state"
    temp_state.mkdir(parents=True, exist_ok=True)
    
    # Mock the paths in state_manager module
    import code.state_manager as sm
    original_metadata = sm.METADATA_FILE
    original_state = sm.STATE_DIR
    original_log = sm.UNRESOLVED_LOG_FILE
    
    sm.METADATA_FILE = str(temp_data_raw / "metadata.json")
    sm.STATE_DIR = str(temp_state)
    sm.UNRESOLVED_LOG_FILE = str(temp_state / "unresolved_realizations.json")
    
    yield {
        "temp_data_raw": temp_data_raw,
        "temp_state": temp_state,
        "sm": sm
    }
    
    # Restore original paths
    sm.METADATA_FILE = original_metadata
    sm.STATE_DIR = original_state
    sm.UNRESOLVED_LOG_FILE = original_log

def test_unresolved_log(setup_test_environment):
    """
    Test that unresolved realizations are properly logged to both
    data/raw/metadata.json and state/unresolved_realizations.json.
    
    This test verifies:
    1. Single realization logging works
    2. Metadata file is created and updated correctly
    3. State log file is created and updated correctly
    4. Summary statistics are accurate
    5. Multiple entries can be logged
    """
    sm = setup_test_environment["sm"]
    temp_data_raw = setup_test_environment["temp_data_raw"]
    temp_state = setup_test_environment["temp_state"]
    
    # Test single realization logging
    sm.log_unresolved_realization(
        realization_id=42,
        delta=0.5,
        L=30,
        reason="convergence_failed",
        additional_info={"iterations": 1000, "final_error": 1e-5}
    )
    
    # Verify metadata.json exists and contains correct data
    metadata_path = temp_data_raw / "metadata.json"
    assert metadata_path.exists(), "metadata.json should be created"
    
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)
    
    assert metadata["project_id"] == "PROJ-308-quantifying-entanglement-entropy-in-rand"
    assert len(metadata["unresolved_realizations"]) == 1
    assert metadata["unresolved_realizations"][0]["realization_id"] == 42
    assert metadata["unresolved_realizations"][0]["delta"] == 0.5
    assert metadata["unresolved_realizations"][0]["L"] == 30
    assert metadata["unresolved_realizations"][0]["reason"] == "convergence_failed"
    assert "timestamp" in metadata["unresolved_realizations"][0]
    assert metadata["unresolved_realizations"][0]["additional_info"]["iterations"] == 1000
    
    # Verify summary is updated
    assert metadata["summary"]["total_unresolved"] == 1
    assert metadata["summary"]["by_reason"]["convergence_failed"] == 1
    
    # Verify state log file exists and contains correct data
    log_path = temp_state / "unresolved_realizations.json"
    assert log_path.exists(), "unresolved_realizations.json should be created"
    
    with open(log_path, 'r') as f:
        log = json.load(f)
    
    assert len(log) == 1
    assert log[0]["realization_id"] == 42
    assert log[0]["delta"] == 0.5
    
    # Test batch logging
    entries = [
        {
            "realization_id": 43,
            "delta": 0.5,
            "L": 30,
            "reason": "max_bond_dimension_reached"
        },
        {
            "realization_id": 44,
            "delta": 0.8,
            "L": 30,
            "reason": "convergence_failed"
        }
    ]
    
    sm.log_unresolved_batch(entries)
    
    # Verify metadata updated
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)
    
    assert len(metadata["unresolved_realizations"]) == 3
    assert metadata["summary"]["total_unresolved"] == 3
    assert metadata["summary"]["by_reason"]["convergence_failed"] == 2
    assert metadata["summary"]["by_reason"]["max_bond_dimension_reached"] == 1
    
    # Verify state log updated
    with open(log_path, 'r') as f:
        log = json.load(f)
    
    assert len(log) == 3
    
    # Test get_unresolved_summary
    summary = sm.get_unresolved_summary()
    assert summary["total_unresolved"] == 3
    assert len(summary["by_reason"]) == 2
    assert len(summary["recent_entries"]) == 3
    
    # Test filtering by delta
    delta_05_entries = sm.get_unresolved_by_delta(0.5)
    assert len(delta_05_entries) == 2
    
    # Test filtering by reason
    convergence_entries = sm.get_unresolved_by_reason("convergence_failed")
    assert len(convergence_entries) == 2
    
    # Test clear function
    sm.clear_unresolved_log()
    
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)
    
    assert len(metadata["unresolved_realizations"]) == 0
    assert metadata["summary"]["total_unresolved"] == 0
    
    with open(log_path, 'r') as f:
        log = json.load(f)
    
    assert len(log) == 0

def test_metadata_structure(setup_test_environment):
    """Test that metadata file has the correct structure."""
    sm = setup_test_environment["sm"]
    temp_data_raw = setup_test_environment["temp_data_raw"]
    
    # Log an entry
    sm.log_unresolved_realization(
        realization_id=1,
        delta=0.1,
        L=20,
        reason="test_reason"
    )
    
    # Load and verify structure
    metadata_path = temp_data_raw / "metadata.json"
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)
    
    # Check required top-level keys
    assert "project_id" in metadata
    assert "created_at" in metadata
    assert "unresolved_realizations" in metadata
    assert "summary" in metadata
    
    # Check summary structure
    assert "total_unresolved" in metadata["summary"]
    assert "by_reason" in metadata["summary"]
    
    # Check entry structure
    entry = metadata["unresolved_realizations"][0]
    assert "realization_id" in entry
    assert "delta" in entry
    assert "L" in entry
    assert "reason" in entry
    assert "timestamp" in entry
    assert "additional_info" in entry

def test_state_directory_structure(setup_test_environment):
    """Test that state directory structure is created correctly."""
    sm = setup_test_environment["sm"]
    temp_state = setup_test_environment["temp_state"]
    
    # Log an entry
    sm.log_unresolved_realization(
        realization_id=1,
        delta=0.1,
        L=20,
        reason="test"
    )
    
    # Verify state directory exists
    assert temp_state.exists()
    assert temp_state.is_dir()
    
    # Verify log file exists in state directory
    log_path = temp_state / "unresolved_realizations.json"
    assert log_path.exists()
    assert log_path.is_file()

def test_empty_log_operations(setup_test_environment):
    """Test operations on empty log."""
    sm = setup_test_environment["sm"]
    
    # Get summary of empty log
    summary = sm.get_unresolved_summary()
    assert summary["total_unresolved"] == 0
    assert summary["by_reason"] == {}
    assert summary["recent_entries"] == []
    
    # Filter on empty log
    assert sm.get_unresolved_by_delta(0.5) == []
    assert sm.get_unresolved_by_reason("any_reason") == []
    
    # Clear empty log
    sm.clear_unresolved_log()
    assert sm.get_unresolved_summary()["total_unresolved"] == 0

def test_multiple_reasons(setup_test_environment):
    """Test handling of multiple different reasons."""
    sm = setup_test_environment["sm"]
    temp_data_raw = setup_test_environment["temp_data_raw"]
    
    reasons = [
        "convergence_failed",
        "max_bond_dimension_reached",
        "numerical_instability",
        "timeout_exceeded"
    ]
    
    for i, reason in enumerate(reasons):
        sm.log_unresolved_realization(
            realization_id=i,
            delta=0.1,
            L=20,
            reason=reason
        )
    
    # Verify counts
    metadata_path = temp_data_raw / "metadata.json"
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)
    
    assert metadata["summary"]["total_unresolved"] == 4
    assert len(metadata["summary"]["by_reason"]) == 4
    
    for reason in reasons:
        assert metadata["summary"]["by_reason"][reason] == 1

def test_additional_info_logging(setup_test_environment):
    """Test that additional_info is properly stored and retrieved."""
    sm = setup_test_environment["sm"]
    temp_data_raw = setup_test_environment["temp_data_raw"]
    
    additional_data = {
        "iterations": 500,
        "final_error": 1.23e-6,
        "bond_dimension": 150,
        "convergence_history": [1e-2, 1e-3, 1e-4, 1e-5],
        "notes": "Test case for additional info"
    }
    
    sm.log_unresolved_realization(
        realization_id=99,
        delta=0.3,
        L=25,
        reason="custom_reason",
        additional_info=additional_data
    )
    
    metadata_path = temp_data_raw / "metadata.json"
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)
    
    entry = metadata["unresolved_realizations"][0]
    assert entry["additional_info"] == additional_data
    assert entry["additional_info"]["iterations"] == 500
    assert entry["additional_info"]["bond_dimension"] == 150