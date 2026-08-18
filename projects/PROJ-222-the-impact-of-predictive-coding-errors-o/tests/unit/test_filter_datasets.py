"""
Unit tests for T014 filtering logic.

These tests verify that the filtering logic correctly excludes datasets
lacking sequential stimuli or predictability manipulations.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import json
import tempfile
import os

from code.filter_datasets import (
    check_sequential_stimuli,
    check_predictability_manipulation,
    log_exclusion,
    log_inclusion,
    load_exclusion_log
)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def exclusion_log_path(temp_dir):
    """Set up exclusion log path for testing."""
    # Override the module-level path for testing
    import code.filter_datasets as fd
    original_path = fd.EXCLUSION_LOG_PATH
    fd.EXCLUSION_LOG_PATH = temp_dir / "test_exclusion_log.json"
    yield fd.EXCLUSION_LOG_PATH
    fd.EXCLUSION_LOG_PATH = original_path

def test_check_sequential_stimuli_with_valid_data():
    """Test that valid sequential data passes the check."""
    df = pd.DataFrame({
        'stimulus_sequence': [1, 2, 3, 4, 5],
        'duration_estimate': [100, 150, 120, 130, 110],
        'participant_id': [1, 1, 1, 1, 1]
    })
    
    is_sequential, reason = check_sequential_stimuli(df, "test_dataset")
    
    assert is_sequential is True
    assert reason is None

def test_check_sequential_stimuli_missing_column():
    """Test that missing sequential column fails the check."""
    df = pd.DataFrame({
        'duration_estimate': [100, 150, 120, 130, 110],
        'participant_id': [1, 1, 1, 1, 1]
    })
    
    is_sequential, reason = check_sequential_stimuli(df, "test_dataset")
    
    assert is_sequential is False
    assert reason is not None
    assert "Missing sequential stimulus column" in reason

def test_check_sequential_stimuli_no_variation():
    """Test that sequential column with no variation fails."""
    df = pd.DataFrame({
        'stimulus_sequence': [1, 1, 1, 1, 1],
        'duration_estimate': [100, 150, 120, 130, 110],
        'participant_id': [1, 1, 1, 1, 1]
    })
    
    is_sequential, reason = check_sequential_stimuli(df, "test_dataset")
    
    assert is_sequential is False
    assert reason is not None
    assert "no sequential variation" in reason

def test_check_predictability_manipulation_with_valid_data():
    """Test that valid predictability data passes the check."""
    df = pd.DataFrame({
        'stimulus_sequence': [1, 2, 3, 4, 5],
        'surprisal': [0.1, 0.5, 0.3, 0.7, 0.2],
        'duration_estimate': [100, 150, 120, 130, 110],
        'participant_id': [1, 1, 1, 1, 1]
    })
    
    has_pred, reason = check_predictability_manipulation(df, "test_dataset")
    
    assert has_pred is True
    assert reason is None

def test_check_predictability_manipulation_missing_column():
    """Test that missing predictability column fails the check."""
    df = pd.DataFrame({
        'stimulus_sequence': [1, 2, 3, 4, 5],
        'duration_estimate': [100, 150, 120, 130, 110],
        'participant_id': [1, 1, 1, 1, 1]
    })
    
    has_pred, reason = check_predictability_manipulation(df, "test_dataset")
    
    assert has_pred is False
    assert reason is not None
    assert "No explicit predictability manipulation column" in reason

def test_check_predictability_manipulation_no_variation():
    """Test that predictability column with no variation fails."""
    df = pd.DataFrame({
        'stimulus_sequence': [1, 2, 3, 4, 5],
        'surprisal': [0.5, 0.5, 0.5, 0.5, 0.5],
        'duration_estimate': [100, 150, 120, 130, 110],
        'participant_id': [1, 1, 1, 1, 1]
    })
    
    has_pred, reason = check_predictability_manipulation(df, "test_dataset")
    
    assert has_pred is False
    assert reason is not None
    assert "no variation for manipulation" in reason

def test_log_exclusion_creates_entry(exclusion_log_path):
    """Test that logging an exclusion creates a proper entry."""
    log_exclusion("test_ds_1", "test_reason", {"detail": "test_detail"})
    
    log_entries = load_exclusion_log()
    assert len(log_entries) == 1
    assert log_entries[0]["dataset_id"] == "test_ds_1"
    assert log_entries[0]["reason"] == "test_reason"
    assert log_entries[0]["details"]["detail"] == "test_detail"
    assert log_entries[0]["status"] == "excluded"

def test_log_inclusion_creates_entry(exclusion_log_path):
    """Test that logging an inclusion creates a proper entry."""
    log_inclusion("test_ds_2", {"test": "data"})
    
    log_entries = load_exclusion_log()
    assert len(log_entries) == 1
    assert log_entries[0]["dataset_id"] == "test_ds_2"
    assert log_entries[0]["status"] == "included"
    assert log_entries[0]["details"]["test"] == "data"

def test_multiple_log_entries(exclusion_log_path):
    """Test that multiple log entries are preserved."""
    log_exclusion("ds_1", "reason_1")
    log_inclusion("ds_2")
    log_exclusion("ds_3", "reason_3")
    
    log_entries = load_exclusion_log()
    assert len(log_entries) == 3
    assert log_entries[0]["dataset_id"] == "ds_1"
    assert log_entries[1]["dataset_id"] == "ds_2"
    assert log_entries[2]["dataset_id"] == "ds_3"
