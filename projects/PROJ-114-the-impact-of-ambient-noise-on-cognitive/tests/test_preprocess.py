"""
Tests for the preprocessing module.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import json

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.preprocess import filter_participants, normalize_reaction_times, aggregate_noise_logs, create_noise_bins

@pytest.fixture
def sample_data():
    return pd.DataFrame({
        'participant_id': ['P1', 'P2', 'P3', 'P4'],
        'valid_hours_ratio': [0.95, 0.70, 0.85, 0.60],
        'task_completion_rate': [0.95, 0.85, 0.92, 0.70],
        'decibel_level': [45, 55, 65, 50],
        'noise_sensitivity_score': [3, 5, 2, 4]
    })

@pytest.fixture
def low_validity_fixture_path():
    """Path to the synthetic fixture for low validity participants."""
    fixture_dir = Path(__file__).parent / "fixtures"
    fixture_dir.mkdir(exist_ok=True)
    fixture_path = fixture_dir / "low_validity_participants.csv"
    
    if not fixture_path.exists():
        # Create the synthetic fixture as required by the task description
        data = {
            'participant_id': ['P_LOW_01', 'P_LOW_02', 'P_LOW_03', 'P_OK_01'],
            'valid_hours_ratio': [0.50, 0.75, 0.60, 0.95],
            'task_completion_rate': [0.60, 0.85, 0.88, 0.98],
            'decibel_level': [40, 50, 60, 45],
            'noise_sensitivity_score': [1, 3, 5, 2]
        }
        df = pd.DataFrame(data)
        df.to_csv(fixture_path, index=False)
    
    return fixture_path

@pytest.fixture
def outlier_fixture_path():
    """Path to the synthetic fixture for outlier reaction times."""
    fixture_dir = Path(__file__).parent / "fixtures"
    fixture_dir.mkdir(exist_ok=True)
    fixture_path = fixture_dir / "outlier_reaction_times.csv"
    
    if not fixture_path.exists():
        # Create the synthetic fixture as required by the task description
        # P1 has an extreme outlier (1000ms) compared to others (~200ms)
        data = {
            'participant_id': ['P1', 'P1', 'P1', 'P1', 'P2'],
            'reaction_time_mean': [200, 210, 190, 1000, 300]
        }
        df = pd.DataFrame(data)
        df.to_csv(fixture_path, index=False)
    
    return fixture_path

def test_filter_participants_excludes_low_validity(sample_data):
    """Test that participants with low validity are excluded."""
    result = filter_participants(sample_data)
    # P2 (0.70 hours) and P4 (0.60 hours, 0.70 completion) should be excluded
    # Thresholds are >= 0.80 valid hours AND >= 0.90 task completion
    assert len(result) == 2
    assert 'P2' not in result['participant_id'].values
    assert 'P4' not in result['participant_id'].values

def test_filter_participants_with_fixture(low_validity_fixture_path):
    """
    Unit test for participant filtering logic using the synthetic fixture 
    fixtures/low_validity_participants.csv as specified in T013.
    
    Verifies that participants with <80% valid hours OR <90% task completion 
    are excluded.
    """
    # Load the real fixture file
    df = pd.read_csv(low_validity_fixture_path)
    
    # Run the filter
    filtered_df = filter_participants(df)
    
    # Expected exclusions based on fixture data:
    # P_LOW_01: 0.50 valid hours (< 0.80) -> EXCLUDE
    # P_LOW_02: 0.75 valid hours (< 0.80) -> EXCLUDE
    # P_LOW_03: 0.60 valid hours (< 0.80) AND 0.88 completion (< 0.90) -> EXCLUDE
    # P_OK_01: 0.95 valid hours (>= 0.80) AND 0.98 completion (>= 0.90) -> KEEP
    
    expected_kept = ['P_OK_01']
    expected_excluded = ['P_LOW_01', 'P_LOW_02', 'P_LOW_03']
    
    assert list(filtered_df['participant_id']) == expected_kept
    
    for excluded_id in expected_excluded:
        assert excluded_id not in filtered_df['participant_id'].values

def test_normalize_reaction_times_removes_outliers(outlier_fixture_path):
    """
    Unit test for MAD-based outlier removal and log-transformation 
    using the synthetic fixture fixtures/outlier_reaction_times.csv as specified in T014.
    
    Verifies that reaction times with absolute deviation > 3.5 * MAD are removed.
    """
    # Load the real fixture file
    df = pd.read_csv(outlier_fixture_path)
    
    # Run the normalization
    result = normalize_reaction_times(df)
    
    # Verify the outlier (1000) was removed
    assert len(result) < len(df), "Outlier removal failed: result length should be less than input"
    assert 1000 not in result['reaction_time_mean'].values, "Outlier value 1000 was not removed"
    
    # Verify that valid values remain
    valid_values = [200, 210, 190, 300]
    for val in valid_values:
        assert val in result['reaction_time_mean'].values, f"Valid value {val} was incorrectly removed"
    
    # Verify log-transformation was applied (values should be transformed)
    # Original values: 200, 210, 190, 300 -> log values should be different
    # We check that the mean of the result is not equal to the mean of the original non-outlier values
    original_non_outlier = df[df['reaction_time_mean'] != 1000]['reaction_time_mean']
    result_mean = result['reaction_time_mean'].mean()
    original_mean = original_non_outlier.mean()
    
    # The log transformation should change the scale significantly
    # We use a tolerance check since log(200) is not 200
    assert abs(result_mean - original_mean) > 10, "Log transformation may not have been applied"