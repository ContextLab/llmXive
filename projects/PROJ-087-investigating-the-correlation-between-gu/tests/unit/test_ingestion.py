import pytest
import pandas as pd
import sys
from pathlib import Path

# Ensure the src directory is on the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.ingestion import filter_antibiotic_use, filter_sleep_data

def test_antibiotic_exclusion_logic():
    """
    Verify that samples with antibiotic_use_last_3m=True are filtered out.
    """
    # Create a mock DataFrame with mixed antibiotic use flags
    data = {
        'sample_id': ['S1', 'S2', 'S3', 'S4', 'S5'],
        'antibiotic_use_last_3m': [True, False, True, False, None],
        'sleep_efficiency': [85, 70, 90, 65, 80],
        'sleep_duration_hours': [7.5, 6.0, 8.0, 5.5, 7.0]
    }
    df = pd.DataFrame(data)

    # Apply the filter
    filtered_df = filter_antibiotic_use(df)

    # Expected: Only rows where antibiotic_use_last_3m is False or None
    # S1 (True) -> Excluded
    # S2 (False) -> Kept
    # S3 (True) -> Excluded
    # S4 (False) -> Kept
    # S5 (None) -> Kept (assuming None implies no known antibiotic use)
    expected_ids = {'S2', 'S4', 'S5'}
    actual_ids = set(filtered_df['sample_id'].tolist())

    assert actual_ids == expected_ids, f"Expected {expected_ids}, got {actual_ids}"
    
    # Verify no True values remain in the filtered column
    assert not filtered_df['antibiotic_use_last_3m'].any(), "Filtered dataset contains True values in antibiotic_use_last_3m"

def test_sleep_data_validation():
    """
    Verify that samples with null sleep_efficiency or sleep_duration_hours are filtered.
    """
    # Create a mock DataFrame with mixed sleep data quality
    data = {
        'sample_id': ['S1', 'S2', 'S3', 'S4', 'S5'],
        'antibiotic_use_last_3m': [False, False, False, False, False],
        'sleep_efficiency': [85.0, None, 90.0, 65.0, None],
        'sleep_duration_hours': [7.5, 6.0, None, 5.5, 7.0]
    }
    df = pd.DataFrame(data)

    # Apply the filter
    filtered_df = filter_sleep_data(df)

    # Expected: Only rows where BOTH sleep_efficiency and sleep_duration_hours are NOT null
    # S1 (85.0, 7.5) -> Kept
    # S2 (None, 6.0) -> Excluded (null efficiency)
    # S3 (90.0, None) -> Excluded (null duration)
    # S4 (65.0, 5.5) -> Kept
    # S5 (None, 7.0) -> Excluded (null efficiency)
    expected_ids = {'S1', 'S4'}
    actual_ids = set(filtered_df['sample_id'].tolist())

    assert actual_ids == expected_ids, f"Expected {expected_ids}, got {actual_ids}"

    # Verify no null values remain in the sleep columns
    assert not filtered_df['sleep_efficiency'].isnull().any(), "Filtered dataset contains null values in sleep_efficiency"
    assert not filtered_df['sleep_duration_hours'].isnull().any(), "Filtered dataset contains null values in sleep_duration_hours"