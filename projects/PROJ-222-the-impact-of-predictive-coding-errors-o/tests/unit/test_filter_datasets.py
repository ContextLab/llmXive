import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import json
import tempfile
import os
from datetime import datetime

# Import the functions to test
from filter_datasets import (
    check_sequential_stimuli,
    check_predictability_manipulation,
    log_exclusion,
    log_inclusion
)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def sequential_dataset():
    """Create a dataset with sequential stimuli."""
    data = {
        'trial_id': range(100),
        'stimulus': ['A', 'B', 'A', 'B', 'C'] * 20,
        'stimulus_sequence': ['A', 'B', 'A', 'B', 'C'] * 20,
        'duration_estimate': np.random.rand(100)
    }
    return pd.DataFrame(data)

@pytest.fixture
def non_sequential_dataset():
    """Create a dataset without sequential stimuli."""
    data = {
        'trial_id': range(100),
        'stimulus': ['A'] * 100,  # Only one stimulus type
        'duration_estimate': np.random.rand(100)
    }
    return pd.DataFrame(data)

@pytest.fixture
def predictability_dataset():
    """Create a dataset with predictability manipulation."""
    data = {
        'trial_id': range(100),
        'stimulus': ['A', 'B'] * 50,
        'condition': ['high_prob', 'low_prob'] * 50,
        'surprisal': [0.1, 2.0] * 50,
        'duration_estimate': np.random.rand(100)
    }
    return pd.DataFrame(data)

@pytest.fixture
def no_predictability_dataset():
    """Create a dataset without predictability manipulation."""
    data = {
        'trial_id': range(100),
        'stimulus': ['A'] * 100,
        'duration_estimate': np.random.rand(100)
    }
    return pd.DataFrame(data)

def test_check_sequential_stimuli_with_sequence(sequential_dataset):
    """Test that sequential stimuli are correctly identified."""
    result = check_sequential_stimuli(sequential_dataset, "test_dataset")
    assert result is None, "Sequential dataset should not be excluded."

def test_check_sequential_stimuli_without_sequence(non_sequential_dataset):
    """Test that non-sequential stimuli are correctly identified."""
    result = check_sequential_stimuli(non_sequential_dataset, "test_dataset")
    assert result is not None, "Non-sequential dataset should be excluded."
    assert "lacks sequential stimuli" in result.lower() or "only one unique" in result.lower()

def test_check_predictability_manipulation_with_manipulation(predictability_dataset):
    """Test that predictability manipulation is correctly identified."""
    result = check_predictability_manipulation(predictability_dataset, "test_dataset")
    assert result is None, "Dataset with predictability manipulation should not be excluded."

def test_check_predictability_manipulation_without_manipulation(no_predictability_dataset):
    """Test that lack of predictability manipulation is correctly identified."""
    result = check_predictability_manipulation(no_predictability_dataset, "test_dataset")
    assert result is not None, "Dataset without predictability manipulation should be excluded."
    assert "lacks predictability" in result.lower()

def test_log_exclusion():
    """Test the log_exclusion function."""
    entry = log_exclusion("test_id", "test reason")
    assert entry["dataset_id"] == "test_id"
    assert entry["reason"] == "test reason"
    assert "timestamp" in entry

def test_log_inclusion(capsys):
    """Test the log_inclusion function."""
    log_inclusion("test_id")
    captured = capsys.readouterr()
    assert "test_id" in captured.out or "test_id" in captured.err
    assert "passed" in captured.out.lower() or "passed" in captured.err.lower()