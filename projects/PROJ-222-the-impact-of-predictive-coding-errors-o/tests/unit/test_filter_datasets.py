import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import json
import tempfile
import os

# Mock the config to avoid path issues in tests
import sys
from unittest.mock import patch, MagicMock

# Add code to path if not already
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from filter_datasets import (
    check_sequential_stimuli,
    check_predictability_manipulation,
    log_exclusion,
    load_exclusion_log,
    save_exclusion_log,
    EXCLUSION_LOG_PATH
)

def test_check_sequential_stimuli_valid():
    """Test with valid sequential data."""
    data = {
        "stimulus_sequence": [1, 2, 3, 1, 2, 3, 1, 2, 3],
        "duration_estimate": [100, 110, 105, 100, 110, 105, 100, 110, 105]
    }
    df = pd.DataFrame(data)
    assert check_sequential_stimuli(df) is True

def test_check_sequential_stimuli_constant():
    """Test with constant sequence (no sequence)."""
    data = {
        "stimulus_sequence": [1, 1, 1, 1, 1],
        "duration_estimate": [100, 100, 100, 100, 100]
    }
    df = pd.DataFrame(data)
    assert check_sequential_stimuli(df) is False

def test_check_sequential_stimuli_missing_column():
    """Test with missing stimulus column."""
    data = {
        "duration_estimate": [100, 100, 100]
    }
    df = pd.DataFrame(data)
    assert check_sequential_stimuli(df) is False

def test_check_predictability_manipulation_with_condition():
    """Test with condition column indicating manipulation."""
    data = {
        "stimulus_sequence": [1, 2, 1, 2],
        "condition": ["high_prob", "low_prob", "high_prob", "low_prob"],
        "duration_estimate": [100, 110, 100, 110]
    }
    df = pd.DataFrame(data)
    assert check_predictability_manipulation(df) is True

def test_check_predictability_manipulation_no_condition():
    """Test with no condition column (assumed random/no manipulation)."""
    data = {
        "stimulus_sequence": [1, 2, 3, 4, 5],
        "duration_estimate": [100, 110, 105, 102, 108]
    }
    df = pd.DataFrame(data)
    # Should return False as per implementation logic requiring structural columns
    assert check_predictability_manipulation(df) is False

def test_log_exclusion_and_load(tmp_path, monkeypatch):
    """Test exclusion logging and loading."""
    # Mock the path
    mock_path = tmp_path / "test_exclusion.json"
    monkeypatch.setattr("filter_datasets.EXCLUSION_LOG_PATH", mock_path)
    
    log_exclusion("test_ds_1", "test_reason", {"detail": "test"})
    
    log = load_exclusion_log()
    assert len(log) == 1
    assert log[0]["dataset_id"] == "test_ds_1"
    assert log[0]["reason"] == "test_reason"
    assert log[0]["status"] == "excluded"
