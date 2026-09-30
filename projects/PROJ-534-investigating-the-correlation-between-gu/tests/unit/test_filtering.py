import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os
import logging
from code.src.data.filtering import filter_cohort, check_zero_variance
from code.src.utils.config import get_processed_data_dir, get_logs_dir

# Fixtures for test data
@pytest.fixture
def sample_cohort_data():
    """Create a sample dataframe matching the schema with mixed ages and missing values."""
    data = {
        'participant_id': ['P001', 'P002', 'P003', 'P004', 'P005', 'P006'],
        'age': [60, 70, 65, 80, 55, 75],
        'sex': ['M', 'F', 'M', 'F', 'M', 'F'],
        'bmi': [24.5, 26.1, 22.0, 28.5, 23.0, 25.5],
        'cognitive_flexibility_score': [85.0, 90.0, np.nan, 78.0, 88.0, 92.0],
        'shannon_diversity': [3.5, 3.8, 3.2, 4.0, 3.6, 3.9],
        'simpson_diversity': [0.92, 0.94, 0.90, 0.96, 0.93, 0.95],
        'chao1': [120.0, 135.0, 110.0, 145.0, 125.0, 140.0],
        'dietary_fiber': [25.0, 30.0, 22.0, 35.0, 28.0, 32.0],
        'antibiotic_use': [False, True, False, True, False, False]
    }
    return pd.DataFrame(data)

@pytest.fixture
def cohort_with_missing():
    """Create a dataframe with explicit NaN/None values in critical columns."""
    data = {
        'participant_id': ['P001', 'P002', 'P003', 'P004', 'P005'],
        'age': [70, 65, np.nan, 80, 75],
        'sex': ['M', 'F', 'M', None, 'F'],
        'bmi': [24.5, np.nan, 22.0, 28.5, 25.5],
        'cognitive_flexibility_score': [85.0, 90.0, 78.0, np.nan, 92.0],
        'shannon_diversity': [3.5, np.nan, 3.2, 4.0, 3.9],
        'simpson_diversity': [0.92, 0.94, 0.90, 0.96, 0.95],
        'chao1': [120.0, 135.0, 110.0, 145.0, 140.0],
        'dietary_fiber': [25.0, 30.0, 22.0, 35.0, 32.0],
        'antibiotic_use': [False, True, False, True, False]
    }
    return pd.DataFrame(data)

@pytest.fixture
def zero_variance_cohort():
    """Create a dataframe where a key metric has zero variance."""
    data = {
        'participant_id': ['P001', 'P002', 'P003'],
        'age': [70, 72, 75],
        'sex': ['M', 'F', 'M'],
        'bmi': [24.5, 26.1, 22.0],
        'cognitive_flexibility_score': [85.0, 90.0, 78.0],
        'shannon_diversity': [3.5, 3.5, 3.5],  # Zero variance
        'simpson_diversity': [0.92, 0.94, 0.90],
        'chao1': [120.0, 135.0, 110.0],
        'dietary_fiber': [25.0, 30.0, 22.0],
        'antibiotic_use': [False, True, False]
    }
    return pd.DataFrame(data)

def test_filter_cohort_age_only(sample_cohort_data):
    """Test that filtering correctly keeps only age >= 65."""
    # Filter for age >= 65
    filtered = filter_cohort(sample_cohort_data, min_age=65)
    
    # Verify all rows meet the age criteria
    assert all(filtered['age'] >= 65), "Filtered data contains rows with age < 65"
    
    # Verify specific expected IDs are present or absent
    expected_ids = {'P002', 'P003', 'P004', 'P006'}
    actual_ids = set(filtered['participant_id'])
    assert actual_ids == expected_ids, f"Expected IDs {expected_ids}, got {actual_ids}"
    
    # Verify original data is unchanged
    assert len(sample_cohort_data) == 6, "Original data was modified"

def test_filter_cohort_null_exclusion(cohort_with_missing):
    """Test that filtering correctly excludes rows with null values in critical columns."""
    critical_columns = [
        'age', 'sex', 'bmi', 'cognitive_flexibility_score', 
        'shannon_diversity', 'simpson_diversity', 'chao1',
        'dietary_fiber', 'antibiotic_use'
    ]
    
    # Filter the cohort (listwise deletion for missing covariates)
    filtered = filter_cohort(cohort_with_missing, min_age=65)
    
    # Verify no nulls in critical columns
    for col in critical_columns:
        assert not filtered[col].isnull().any(), f"Column {col} contains null values after filtering"
    
    # Verify expected rows are kept/removed
    # P001: age 70, all non-null -> KEEP
    # P002: age 65, bmi null -> DROP
    # P003: age null -> DROP
    # P004: age 80, sex null -> DROP
    # P005: age 75, shannon null -> DROP
    expected_ids = {'P001'}
    actual_ids = set(filtered['participant_id'])
    assert actual_ids == expected_ids, f"Expected IDs {expected_ids}, got {actual_ids}"
    
    # Verify original data is unchanged
    assert len(cohort_with_missing) == 5, "Original data was modified"

def test_check_zero_variance_with_normal_data(sample_cohort_data):
    """Test zero variance check on data with variance."""
    result, message = check_zero_variance(sample_cohort_data, 'shannon_diversity')
    assert result is False, "Detected zero variance in data with variance"
    assert "zero variance" not in message.lower()

def test_check_zero_variance_with_constant_data(zero_variance_cohort):
    """Test zero variance check on data without variance."""
    result, message = check_zero_variance(zero_variance_cohort, 'shannon_diversity')
    assert result is True, "Failed to detect zero variance in constant data"
    assert "zero variance" in message.lower()

def test_filter_cohort_handles_empty_dataframe():
    """Test that filtering an empty dataframe returns an empty dataframe."""
    empty_df = pd.DataFrame(columns=[
        'participant_id', 'age', 'sex', 'bmi', 'cognitive_flexibility_score',
        'shannon_diversity', 'simpson_diversity', 'chao1', 'dietary_fiber', 'antibiotic_use'
    ])
    
    filtered = filter_cohort(empty_df, min_age=65)
    
    assert filtered.empty, "Filtering empty dataframe did not return empty dataframe"
    assert len(filtered) == 0, "Filtered dataframe has rows"

def test_filter_cohort_logging(cohort_with_missing, caplog):
    """Test that filtering logs the number of dropped rows."""
    with caplog.at_level(logging.INFO):
        filtered = filter_cohort(cohort_with_missing, min_age=65)
    
    # Check that logging occurred
    assert any("dropped" in record.message.lower() for record in caplog.records), "No logging about dropped rows"
    assert any("null" in record.message.lower() for record in caplog.records), "No logging about null values"