import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.data.filtering import filter_cohort, check_zero_variance, REQUIRED_COVARIATES, CRITICAL_METRICS

@pytest.fixture
def sample_cohort_data():
    """Generate a sample cohort with mixed ages and complete data."""
    data = {
        'participant_id': [f'P{i}' for i in range(10)],
        'age': [60, 65, 70, 75, 80, 62, 68, 72, 64, 69],
        'sex': ['Male', 'Female', 'Male', 'Female', 'Male', 'Female', 'Male', 'Female', 'Male', 'Female'],
        'bmi': [24.5, 26.1, 22.3, 28.0, 25.5, 24.0, 27.2, 23.5, 26.8, 25.0],
        'cognitive_flexibility_score': [0.8, 0.75, 0.9, 0.65, 0.85, 0.78, 0.92, 0.70, 0.82, 0.88],
        'shannon_diversity': [3.2, 3.5, 3.1, 3.8, 3.4, 3.3, 3.6, 3.0, 3.7, 3.45],
        'simpson_diversity': [0.92, 0.94, 0.91, 0.95, 0.93, 0.92, 0.94, 0.90, 0.95, 0.93],
        'chao1': [4.5, 4.8, 4.2, 5.0, 4.6, 4.4, 4.9, 4.1, 5.1, 4.7],
        'dietary_fiber': [25.0, 30.0, 28.0, 35.0, 22.0, 27.0, 31.0, 26.0, 33.0, 29.0],
        'antibiotic_use': [False, True, False, False, True, False, True, False, False, True]
    }
    return pd.DataFrame(data)

@pytest.fixture
def cohort_with_missing():
    """Generate a cohort with missing values in critical fields."""
    data = {
        'participant_id': [f'P{i}' for i in range(5)],
        'age': [65, 70, 75, 60, 80],
        'sex': ['Male', 'Female', 'Male', 'Female', 'Male'],
        'bmi': [24.5, np.nan, 22.3, 28.0, 25.5],
        'cognitive_flexibility_score': [0.8, 0.75, np.nan, 0.65, 0.85],
        'shannon_diversity': [3.2, 3.5, 3.1, np.nan, 3.4],
        'simpson_diversity': [0.92, 0.94, 0.91, 0.95, 0.93],
        'chao1': [4.5, 4.8, 4.2, 5.0, 4.6],
        'dietary_fiber': [25.0, 30.0, 28.0, 22.0, 27.0],
        'antibiotic_use': [False, True, False, False, True]
    }
    return pd.DataFrame(data)

@pytest.fixture
def zero_variance_cohort():
    """Generate a cohort where a critical metric has zero variance."""
    data = {
        'participant_id': [f'P{i}' for i in range(5)],
        'age': [65, 70, 75, 80, 85],
        'sex': ['Male', 'Female', 'Male', 'Female', 'Male'],
        'bmi': [24.5, 26.1, 22.3, 28.0, 25.5],
        'cognitive_flexibility_score': [0.8, 0.8, 0.8, 0.8, 0.8], # Zero variance
        'shannon_diversity': [3.2, 3.5, 3.1, 3.8, 3.4],
        'simpson_diversity': [0.92, 0.94, 0.91, 0.95, 0.93],
        'chao1': [4.5, 4.8, 4.2, 5.0, 4.6],
        'dietary_fiber': [25.0, 30.0, 28.0, 22.0, 27.0],
        'antibiotic_use': [False, True, False, False, True]
    }
    return pd.DataFrame(data)

def test_filter_cohort_age_only(sample_cohort_data):
    """Test that filtering correctly keeps only age >= 65."""
    filtered = filter_cohort(sample_cohort_data, min_age=65)
    
    # All ages should be >= 65
    assert all(filtered['age'] >= 65)
    # Original had 2 entries < 65 (60, 62, 64 -> 3 entries actually)
    # 60, 62, 64 are < 65. So 3 dropped.
    assert len(filtered) == len(sample_cohort_data) - 3

def test_filter_cohort_listwise_deletion(cohort_with_missing):
    """Test that listwise deletion removes rows with missing critical values or covariates."""
    filtered = filter_cohort(cohort_with_missing)
    
    # Check no nulls in critical metrics
    assert filtered['cognitive_flexibility_score'].notna().all()
    assert filtered['shannon_diversity'].notna().all()
    
    # Check no nulls in required covariates
    for col in REQUIRED_COVARIATES:
        if col in filtered.columns:
            assert filtered[col].notna().all()
    
    # Original had 5 rows.
    # P1: BMI null -> dropped
    # P2: Cognitive null -> dropped
    # P3: Shannon null -> dropped
    # P0 and P4 are complete.
    assert len(filtered) == 2

def test_check_zero_variance_with_normal_data(sample_cohort_data):
    """Test zero variance check on normal data."""
    assert not check_zero_variance(sample_cohort_data, 'age')
    assert not check_zero_variance(sample_cohort_data, 'shannon_diversity')

def test_check_zero_variance_with_constant_data(zero_variance_cohort):
    """Test zero variance check on constant data."""
    assert check_zero_variance(zero_variance_cohort, 'cognitive_flexibility_score')

def test_filter_cohort_handles_empty_dataframe():
    """Test that filtering an empty dataframe raises an error."""
    empty_df = pd.DataFrame()
    with pytest.raises(ValueError):
        filter_cohort(empty_df)
