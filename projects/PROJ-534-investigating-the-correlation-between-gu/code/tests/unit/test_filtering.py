import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os
import logging

from code.src.data.filtering import filter_cohort, check_zero_variance, REQUIRED_COVARIATES

@pytest.fixture
def sample_cohort_data():
    """Create a sample cohort DataFrame with all required fields."""
    data = {
        "participant_id": [f"p{i:03d}" for i in range(1, 11)],
        "age": [70, 65, 80, 55, 72, 68, 75, 60, 82, 69],
        "sex": ["Male", "Female", "Male", "Female", "Male", "Female", "Male", "Female", "Male", "Female"],
        "bmi": [24.5, 22.1, 26.3, 21.0, 25.0, 23.5, 27.0, 20.5, 28.0, 24.0],
        "cognitive_flexibility_score": [85.0, 88.0, 79.0, 90.0, 82.0, 86.0, 80.0, 91.0, 78.0, 84.0],
        "shannon_diversity": [3.2, 3.5, 3.1, 3.8, 3.3, 3.4, 3.0, 3.9, 2.9, 3.3],
        "simpson_diversity": [0.92, 0.95, 0.90, 0.97, 0.93, 0.94, 0.89, 0.98, 0.88, 0.93],
        "chao1": [120.0, 135.0, 115.0, 145.0, 125.0, 130.0, 110.0, 150.0, 105.0, 128.0],
        "dietary_fiber_intake": [25.0, 30.0, 22.0, 35.0, 27.0, 28.0, 20.0, 38.0, 18.0, 26.0],
        "antibiotic_use_history": [True, False, True, False, False, True, True, False, True, False]
    }
    return pd.DataFrame(data)

@pytest.fixture
def cohort_with_missing():
    """Create a cohort with missing values in covariates."""
    data = {
        "participant_id": [f"p{i:03d}" for i in range(1, 8)],
        "age": [70, 65, 80, 55, 72, 68, 75],
        "sex": ["Male", "Female", "Male", "Female", "Male", None, "Male"],
        "bmi": [24.5, None, 26.3, 21.0, 25.0, 23.5, 27.0],
        "cognitive_flexibility_score": [85.0, 88.0, 79.0, 90.0, 82.0, 86.0, 80.0],
        "shannon_diversity": [3.2, 3.5, 3.1, 3.8, 3.3, 3.4, 3.0],
        "dietary_fiber_intake": [25.0, 30.0, None, 35.0, 27.0, 28.0, 20.0],
        "antibiotic_use_history": [True, False, True, False, False, True, True]
    }
    return pd.DataFrame(data)

@pytest.fixture
def zero_variance_cohort():
    """Create a cohort with zero variance in one column."""
    data = {
        "participant_id": [f"p{i:03d}" for i in range(1, 6)],
        "age": [70, 65, 80, 72, 68],
        "sex": ["Male", "Male", "Male", "Male", "Male"],
        "bmi": [24.5, 24.5, 24.5, 24.5, 24.5],
        "cognitive_flexibility_score": [85.0, 88.0, 79.0, 82.0, 86.0],
        "shannon_diversity": [3.2, 3.5, 3.1, 3.3, 3.4],
        "dietary_fiber_intake": [25.0, 30.0, 22.0, 27.0, 28.0],
        "antibiotic_use_history": [True, True, True, True, True]
    }
    return pd.DataFrame(data)

def test_filter_cohort_age_only(sample_cohort_data):
    """Test that age filtering works correctly."""
    # All participants are >= 55, but only those >= 65 should remain
    filtered_df, dropped_count = filter_cohort(sample_cohort_data, min_age=65)
    
    # Check that all remaining ages are >= 65
    assert all(filtered_df["age"] >= 65)
    
    # Original had 10 rows, age < 65 are: 55, 60 -> 2 rows dropped by age
    # No missing values in covariates, so no additional drops
    # Expected: 10 - 2 = 8 rows
    assert len(filtered_df) == 8

def test_filter_cohort_listwise_deletion(cohort_with_missing):
    """Test listwise deletion for missing covariates."""
    # Initial count: 7 rows
    # Age filter (>= 65): drops p004 (55) -> 6 rows remain
    # Missing covariates:
    #   p002: missing BMI
    #   p003: missing dietary_fiber_intake
    #   p006: missing sex
    #   p007: no missing
    # After listwise deletion: only p001, p005, p007 should remain (3 rows)
    
    filtered_df, dropped_count = filter_cohort(cohort_with_missing, min_age=65)
    
    # Verify no missing values in required covariates
    for col in REQUIRED_COVARIATES:
        if col in filtered_df.columns:
            assert not filtered_df[col].isna().any(), f"Column {col} still has missing values"
    
    # Expected: 3 rows remain (p001, p005, p007)
    assert len(filtered_df) == 3
    
    # Dropped count should reflect listwise deletion
    # Total dropped = 7 - 3 = 4
    # Age filter dropped 1 (p004)
    # Listwise deletion dropped 3 (p002, p003, p006)
    assert dropped_count == 3

def test_check_zero_variance_with_normal_data(sample_cohort_data):
    """Test zero variance check on normal data."""
    # bmi has variance, should return False
    assert not check_zero_variance(sample_cohort_data, "bmi")
    
    # Age has variance
    assert not check_zero_variance(sample_cohort_data, "age")

def test_check_zero_variance_with_constant_data(zero_variance_cohort):
    """Test zero variance check on constant data."""
    # All males -> zero variance
    assert check_zero_variance(zero_variance_cohort, "sex")
    
    # All BMI 24.5 -> zero variance
    assert check_zero_variance(zero_variance_cohort, "bmi")
    
    # All True -> zero variance
    assert check_zero_variance(zero_variance_cohort, "antibiotic_use_history")

def test_filter_cohort_handles_empty_dataframe():
    """Test filtering on an empty DataFrame."""
    empty_df = pd.DataFrame(columns=["participant_id", "age", "sex", "bmi", "cognitive_flexibility_score", "shannon_diversity"])
    
    filtered_df, dropped_count = filter_cohort(empty_df, min_age=65)
    
    assert len(filtered_df) == 0
    assert dropped_count == 0
