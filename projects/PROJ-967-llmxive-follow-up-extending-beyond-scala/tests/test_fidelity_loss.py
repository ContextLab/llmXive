"""
Unit tests for T024: Dimensional Fidelity Loss calculation.
"""
import json
import os
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# Import the module functions
import sys
sys.path.insert(0, 'code')
from fidelity_loss import calculate_fidelity_loss, save_summary, save_exclusions_log


def create_test_dataframe():
    """Create a mock dataframe for testing."""
    data = {
        'sample_id': [0, 1, 2, 3, 4],
        'student_scalar': [1.0, 2.0, np.nan, 4.0, 5.0],
        'primary_dimension': [0, 1, 2, 3, 5],  # 5 is out of bounds
        'human_annotations': [
            [1.1, 2.2, 3.3, 4.4],  # Valid
            [0.9, 1.9, 3.1, 4.0],  # Valid
            [1.0, 2.0, 3.0, 4.0],  # Valid but student_scalar is NaN
            [3.9, 4.0, 5.0, 6.0],  # Valid
            [1.0, 2.0, 3.0, 4.0]   # Valid but dimension out of bounds
        ]
    }
    return pd.DataFrame(data)


def test_calculate_fidelity_loss_valid_samples():
    """Test calculation on valid samples."""
    df = create_test_dataframe()
    # Mock logger
    class MockLogger:
        def info(self, msg): pass
        def error(self, msg): pass
    
    cleaned_df, exclusions, stats = calculate_fidelity_loss(df, MockLogger())
    
    # Sample 0: |1.0 - 1.1| = 0.1
    # Sample 1: |2.0 - 1.9| = 0.1
    # Sample 3: |4.0 - 4.0| = 0.0
    # Sample 2: Excluded (NaN student_scalar)
    # Sample 4: Excluded (dimension out of bounds)
    
    assert len(cleaned_df) == 5
    assert len(exclusions) == 2
    
    # Check specific values
    assert abs(cleaned_df.iloc[0]['fidelity_loss'] - 0.1) < 1e-6
    assert abs(cleaned_df.iloc[1]['fidelity_loss'] - 0.1) < 1e-6
    assert abs(cleaned_df.iloc[3]['fidelity_loss'] - 0.0) < 1e-6
    
    # Check NaN for excluded
    assert pd.isna(cleaned_df.iloc[2]['fidelity_loss'])
    assert pd.isna(cleaned_df.iloc[4]['fidelity_loss'])
    
    assert stats['count'] == 3
    assert stats['excluded_count'] == 2


def test_calculate_fidelity_loss_missing_primary_dimension():
    """Test exclusion when primary_dimension is missing."""
    data = {
        'sample_id': [10],
        'student_scalar': [1.0],
        'primary_dimension': [np.nan],
        'human_annotations': [[1.0, 2.0, 3.0, 4.0]]
    }
    df = pd.DataFrame(data)
    
    class MockLogger:
        def info(self, msg): pass
        def error(self, msg): pass
    
    _, exclusions, _ = calculate_fidelity_loss(df, MockLogger())
    
    assert len(exclusions) == 1
    assert exclusions[0]['reason'] == 'missing_or_invalid_primary_dimension'


def test_calculate_fidelity_loss_missing_annotation():
    """Test exclusion when human_annotations is missing for target dimension."""
    data = {
        'sample_id': [11],
        'student_scalar': [1.0],
        'primary_dimension': [0],
        'human_annotations': [np.nan]
    }
    df = pd.DataFrame(data)
    
    class MockLogger:
        def info(self, msg): pass
        def error(self, msg): pass
    
    _, exclusions, _ = calculate_fidelity_loss(df, MockLogger())
    
    assert len(exclusions) == 1
    assert exclusions[0]['reason'] == 'missing_human_annotations'


def test_save_summary(tmp_path):
    """Test saving summary statistics to JSON."""
    stats = {
        "count": 10,
        "excluded_count": 2,
        "mean": 0.5,
        "median": 0.4,
        "std": 0.1,
        "min": 0.1,
        "max": 0.9
    }
    output_path = tmp_path / "summary.json"
    save_summary(stats, output_path, MockLogger())
    
    assert output_path.exists()
    with open(output_path, 'r') as f:
        loaded = json.load(f)
    assert loaded == stats


def test_save_exclusions_log(tmp_path):
    """Test saving exclusions log to JSON."""
    exclusions = [
        {"sample_id": 1, "reason": "missing_data"},
        {"sample_id": 2, "reason": "invalid_dimension"}
    ]
    output_path = tmp_path / "exclusions.json"
    save_exclusions_log(exclusions, output_path, MockLogger())
    
    assert output_path.exists()
    with open(output_path, 'r') as f:
        loaded = json.load(f)
    assert loaded == exclusions


class MockLogger:
    def info(self, msg): pass
    def error(self, msg): pass
    def warning(self, msg): pass
    def debug(self, msg): pass