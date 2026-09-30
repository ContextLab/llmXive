"""
Unit tests for the data filtering module.
Tests cover age filtering, null exclusion, zero-variance detection,
and listwise deletion logic.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os
import sys

# Ensure the project root is in the path for imports
# This assumes the test is run from the project root or via pytest discovery
try:
    from code.src.data.filtering import filter_cohort, check_zero_variance
except ImportError:
    # Fallback for different directory structures if necessary
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from code.src.data.filtering import filter_cohort, check_zero_variance

@pytest.fixture
def sample_cohort_data():
    """
    Creates a sample DataFrame mimicking the structure of the filtered cohort.
    Includes a mix of ages, missing values, and valid data.
    """
    data = {
        'participant_id': ['P01', 'P02', 'P03', 'P04', 'P05', 'P06', 'P07'],
        'age': [60, 65, 70, 55, 80, 65, 75],
        'sex': ['M', 'F', 'M', 'F', 'M', 'F', 'M'],
        'bmi': [22.5, 24.1, 25.0, 19.5, 28.0, None, 23.5],
        'cognitive_flexibility_score': [0.85, 0.72, 0.91, 0.65, 0.88, 0.79, 0.82],
        'shannon_diversity': [3.2, 3.5, 3.1, 2.9, 3.8, 3.4, 3.6],
        'simpson_diversity': [0.85, 0.88, 0.82, 0.75, 0.92, 0.87, 0.89],
        'chao1': [4.0, 4.2, 3.9, 3.5, 4.5, 4.1, 4.3],
        'dietary_fiber': [25.0, 30.0, 28.0, 15.0, 35.0, 22.0, 29.0],
        'antibiotic_use': [False, True, False, False, True, False, False]
    }
    return pd.DataFrame(data)

@pytest.fixture
def cohort_with_missing():
    """
    Creates a DataFrame with intentional missing values in critical columns
    to test listwise deletion.
    """
    data = {
        'participant_id': ['P01', 'P02', 'P03', 'P04', 'P05'],
        'age': [65, 70, 80, 60, 75],
        'sex': ['M', 'F', 'M', 'F', 'M'],
        'bmi': [22.5, 24.1, None, 19.5, 28.0],
        'cognitive_flexibility_score': [0.85, 0.72, 0.91, 0.65, 0.88],
        'shannon_diversity': [3.2, 3.5, 3.1, None, 3.8],
        'simpson_diversity': [0.85, 0.88, 0.82, 0.75, 0.92],
        'chao1': [4.0, 4.2, 3.9, 3.5, 4.5],
        'dietary_fiber': [25.0, 30.0, 28.0, 15.0, 35.0],
        'antibiotic_use': [False, True, False, False, True]
    }
    return pd.DataFrame(data)

@pytest.fixture
def zero_variance_cohort():
    """
    Creates a DataFrame where one column has zero variance (constant value).
    """
    data = {
        'participant_id': ['P01', 'P02', 'P03'],
        'age': [65, 70, 75],
        'sex': ['M', 'M', 'M'],  # Zero variance if only one category
        'bmi': [22.5, 24.1, 25.0],
        'cognitive_flexibility_score': [0.85, 0.72, 0.91],
        'shannon_diversity': [3.2, 3.5, 3.1],
        'simpson_diversity': [0.85, 0.88, 0.82],
        'chao1': [4.0, 4.2, 3.9],
        'dietary_fiber': [25.0, 30.0, 28.0],
        'antibiotic_use': [True, True, True]
    }
    return pd.DataFrame(data)

def test_filter_cohort_age_only(sample_cohort_data):
    """
    Test T014: Unit test for age filtering logic.
    Verifies that only participants with age >= 65 are retained.
    """
    # Expected count: P02 (65), P03 (70), P05 (80), P06 (65), P07 (75) -> 5 rows
    # P01 (60) and P04 (55) should be dropped.
    filtered_df, dropped_count = filter_cohort(
        sample_cohort_data,
        min_age=65,
        require_null_columns=None,
        require_covariates=None
    )
    
    assert len(filtered_df) == 5, f"Expected 5 rows after age filtering, got {len(filtered_df)}"
    assert all(filtered_df['age'] >= 65), "All remaining participants must be >= 65 years old"
    
    # Verify specific IDs are dropped
    assert 'P01' not in filtered_df['participant_id'].values
    assert 'P04' not in filtered_df['participant_id'].values
    
    # Verify specific IDs are kept
    assert 'P02' in filtered_df['participant_id'].values
    assert 'P03' in filtered_df['participant_id'].values
    assert 'P05' in filtered_df['participant_id'].values
    assert 'P06' in filtered_df['participant_id'].values
    assert 'P07' in filtered_df['participant_id'].values

def test_filter_cohort_listwise_deletion(cohort_with_missing):
    """
    Test listwise deletion for missing covariates and metrics.
    """
    # P03 has missing BMI, P04 has missing Shannon. Both should be dropped.
    # P01, P02, P05 are complete.
    filtered_df, dropped_count = filter_cohort(
        cohort_with_missing,
        min_age=60,
        require_null_columns=['cognitive_flexibility_score', 'shannon_diversity'],
        require_covariates=['age', 'sex', 'bmi', 'dietary_fiber', 'antibiotic_use']
    )
    
    # Expected: P01, P02, P05 remain. P03 (missing BMI), P04 (missing Shannon) dropped.
    assert len(filtered_df) == 3, f"Expected 3 rows after listwise deletion, got {len(filtered_df)}"
    assert 'P03' not in filtered_df['participant_id'].values
    assert 'P04' not in filtered_df['participant_id'].values

def test_check_zero_variance_with_normal_data(sample_cohort_data):
    """
    Test that normal data returns no zero-variance columns.
    """
    zero_var_cols = check_zero_variance(sample_cohort_data)
    assert len(zero_var_cols) == 0, f"Expected no zero-variance columns, found: {zero_var_cols}"

def test_check_zero_variance_with_constant_data(zero_variance_cohort):
    """
    Test detection of zero-variance columns.
    """
    zero_var_cols = check_zero_variance(zero_variance_cohort)
    # 'sex' is constant 'M', 'antibiotic_use' is constant True
    assert 'sex' in zero_var_cols, "Expected 'sex' to be detected as zero variance"
    assert 'antibiotic_use' in zero_var_cols, "Expected 'antibiotic_use' to be detected as zero variance"

def test_filter_cohort_handles_empty_dataframe():
    """
    Test that filtering an empty DataFrame does not crash.
    """
    empty_df = pd.DataFrame(columns=['participant_id', 'age', 'sex'])
    filtered_df, dropped_count = filter_cohort(
        empty_df,
        min_age=65,
        require_null_columns=None,
        require_covariates=None
    )
    assert len(filtered_df) == 0
    assert dropped_count == 0