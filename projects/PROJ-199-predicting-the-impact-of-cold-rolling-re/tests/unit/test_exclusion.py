"""
Unit tests for the exclusion logic module.
"""
import pandas as pd
import pytest
from pathlib import Path
import tempfile
import os

# Import the functions to test
from data.exclusion import calculate_reliability_metrics, apply_exclusion_logic, RELIABILITY_THRESHOLD

@pytest.fixture
def sample_data():
    """Create a mock DataFrame simulating EBSD data with filtering info."""
    data = {
        'sample_id': ['S1', 'S1', 'S1', 'S2', 'S2', 'S3', 'S3', 'S3', 'S3'],
        'x': [1.0, 1.1, 1.2, 2.0, 2.1, 3.0, 3.1, 3.2, 3.3],
        'y': [1.0, 1.1, 1.2, 2.0, 2.1, 3.0, 3.1, 3.2, 3.3],
        'is_filtered': [False, False, True, True, True, False, False, False, False],
        # Simulate pre-calculated counts if needed, otherwise function derives them
        'original_point_count': [3, 3, 3, 2, 2, 4, 4, 4, 4],
        'filtered_point_count': [1, 1, 1, 2, 2, 0, 0, 0, 0]
    }
    return pd.DataFrame(data)

def test_calculate_reliability_metrics_basic(sample_data):
    """Test that reliability metrics are calculated correctly."""
    df = sample_data.copy()
    
    # Remove pre-calculated counts to force derivation
    df = df.drop(columns=['original_point_count', 'filtered_point_count'])
    
    result = calculate_reliability_metrics(df)
    
    # Check that new columns exist
    assert 'reliability_ratio' in result.columns
    assert 'is_low_reliability' in result.columns
    assert 'status' in result.columns

    # Verify specific values
    # S1: 1 filtered / 3 total = 0.333 -> Valid
    # S2: 2 filtered / 2 total = 1.0 -> Low Reliability
    # S3: 0 filtered / 4 total = 0.0 -> Valid
    
    s1_data = result[result['sample_id'] == 'S1']
    assert s1_data['is_low_reliability'].iloc[0] == False
    assert s1_data['status'].iloc[0] == 'valid'
    assert abs(s1_data['reliability_ratio'].iloc[0] - 1/3) < 0.01

    s2_data = result[result['sample_id'] == 'S2']
    assert s2_data['is_low_reliability'].iloc[0] == True
    assert s2_data['status'].iloc[0] == 'low_reliability'
    assert s2_data['reliability_ratio'].iloc[0] == 1.0

    s3_data = result[result['sample_id'] == 'S3']
    assert s3_data['is_low_reliability'].iloc[0] == False
    assert s3_data['status'].iloc[0] == 'valid'
    assert s3_data['reliability_ratio'].iloc[0] == 0.0

def test_apply_exclusion_logic_removes_low_reliability(sample_data):
    """Test that apply_exclusion_logic removes samples with >50% filtered points."""
    df = sample_data.copy()
    df = df.drop(columns=['original_point_count', 'filtered_point_count'])
    df_with_metrics = calculate_reliability_metrics(df)
    
    clean_df = apply_exclusion_logic(df_with_metrics)
    
    # S2 should be removed
    assert 'S2' not in clean_df['sample_id'].unique()
    
    # S1 and S3 should remain
    assert 'S1' in clean_df['sample_id'].unique()
    assert 'S3' in clean_df['sample_id'].unique()

    # Check row counts
    assert len(clean_df) == 3 + 4  # S1 (3 rows) + S3 (4 rows)

def test_apply_exclusion_logic_with_output_path(sample_data):
    """Test that exclusion report is written correctly."""
    df = sample_data.copy()
    df = df.drop(columns=['original_point_count', 'filtered_point_count'])
    df_with_metrics = calculate_reliability_metrics(df)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        report_path = Path(tmpdir) / "report.csv"
        clean_df = apply_exclusion_logic(df_with_metrics, output_path=report_path)
        
        assert report_path.exists()
        
        report_df = pd.read_csv(report_path)
        assert 'status' in report_df.columns
        assert 'excluded' in report_df['status'].values
        assert 'valid' in report_df['status'].values

def test_threshold_boundary():
    """Test the exact 50% threshold behavior."""
    # Create data where exactly 50% is filtered
    # 2 points, 1 filtered -> 0.5 ratio -> Should be VALID (since > 0.5 is excluded)
    data = {
        'sample_id': ['A', 'A'],
        'x': [1, 2],
        'y': [1, 2],
        'is_filtered': [True, False],
    }
    df = pd.DataFrame(data)
    
    result = calculate_reliability_metrics(df)
    assert result['is_low_reliability'].iloc[0] == False
    assert result['status'].iloc[0] == 'valid'

    # Create data where 51% is filtered (e.g., 100 points, 51 filtered)
    # We simulate this with counts
    data2 = {
        'sample_id': ['B', 'B', 'B'], # 3 rows to represent 100 points? No, let's use explicit counts
        'x': [1, 2, 3],
        'y': [1, 2, 3],
        'is_filtered': [True, True, False],
        'original_point_count': [3, 3, 3],
        'filtered_point_count': [2, 2, 2] # 2/3 = 0.66 > 0.5
    }
    df2 = pd.DataFrame(data2)
    result2 = calculate_reliability_metrics(df2)
    assert result2['is_low_reliability'].iloc[0] == True
    assert result2['status'].iloc[0] == 'low_reliability'