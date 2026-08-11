import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os
from code.src.data.filtering import check_zero_variance, filter_cohort

@pytest.fixture
def sample_cohort_data():
    """Create a sample cohort dataframe for testing."""
    np.random.seed(42)
    n = 100
    data = {
        'participant_id': range(1, n + 1),
        'age': np.random.randint(50, 85, n),
        'sex': np.random.choice(['M', 'F'], n),
        'bmi': np.random.normal(25, 4, n),
        'fiber': np.random.normal(20, 5, n),
        'antibiotics': np.random.choice([0, 1], n),
        'shannon_diversity': np.random.normal(3.5, 0.5, n),
        'cognitive_score': np.random.normal(85, 10, n)
    }
    return pd.DataFrame(data)

@pytest.fixture
def zero_variance_cohort():
    """Create a cohort with zero variance in target metrics."""
    n = 50
    data = {
        'participant_id': range(1, n + 1),
        'age': [70] * n,  # All same age
        'sex': ['M'] * n,
        'bmi': [25.0] * n,
        'fiber': [20.0] * n,
        'antibiotics': [0] * n,
        'shannon_diversity': [3.5] * n,  # Zero variance
        'cognitive_score': [85.0] * n    # Zero variance
    }
    return pd.DataFrame(data)

def test_check_zero_variance_with_normal_data(sample_cohort_data):
    """Test that normal data returns no zero variance."""
    has_zero_var, zero_cols = check_zero_variance(sample_cohort_data, ['shannon_diversity', 'cognitive_score'])
    assert has_zero_var == False
    assert zero_cols == []

def test_check_zero_variance_with_constant_data(zero_variance_cohort):
    """Test that constant data is detected as zero variance."""
    has_zero_var, zero_cols = check_zero_variance(zero_variance_cohort, ['shannon_diversity', 'cognitive_score'])
    assert has_zero_var == True
    assert 'shannon_diversity' in zero_cols
    assert 'cognitive_score' in zero_cols

def test_check_zero_variance_partial(zero_variance_cohort):
    """Test detection when only some columns have zero variance."""
    # Create data with one zero-variance column
    df = zero_variance_cohort.copy()
    df['cognitive_score'] = np.random.normal(85, 10, len(df))
    
    has_zero_var, zero_cols = check_zero_variance(df, ['shannon_diversity', 'cognitive_score'])
    assert has_zero_var == True
    assert 'shannon_diversity' in zero_cols
    assert 'cognitive_score' not in zero_cols

def test_filter_cohort_detects_zero_variance(zero_variance_cohort):
    """Test that filter_cohort properly detects and flags zero variance."""
    filtered = filter_cohort(
        zero_variance_cohort,
        min_age=65,
        required_covariates=['age', 'sex', 'bmi', 'fiber', 'antibiotics'],
        target_metrics=['shannon_diversity', 'cognitive_score'],
        impute_missing=False
    )
    
    assert filtered.attrs.get('zero_variance_detected', False) == True
    assert 'shannon_diversity' in filtered.attrs.get('zero_variance_columns', [])
    assert 'cognitive_score' in filtered.attrs.get('zero_variance_columns', [])

def test_filter_cohort_normal_data(sample_cohort_data):
    """Test filtering with normal data (no zero variance)."""
    filtered = filter_cohort(
        sample_cohort_data,
        min_age=65,
        required_covariates=['age', 'sex', 'bmi', 'fiber', 'antibiotics'],
        target_metrics=['shannon_diversity', 'cognitive_score'],
        impute_missing=False
    )
    
    assert filtered.attrs.get('zero_variance_detected', False) == False
    assert len(filtered) < len(sample_cohort_data)  # Should be filtered by age and non-null
    assert all(filtered['age'] >= 65)
    assert filtered['shannon_diversity'].notna().all()
    assert filtered['cognitive_score'].notna().all()

def test_filter_cohort_with_imputation():
    """Test filtering with missing covariates and imputation."""
    n = 50
    data = {
        'participant_id': range(1, n + 1),
        'age': np.random.randint(65, 85, n),
        'sex': np.random.choice(['M', 'F'], n),
        'bmi': [np.nan] * 10 + list(np.random.normal(25, 4, 40)),  # Missing values
        'fiber': np.random.normal(20, 5, n),
        'antibiotics': np.random.choice([0, 1], n),
        'shannon_diversity': np.random.normal(3.5, 0.5, n),
        'cognitive_score': np.random.normal(85, 10, n)
    }
    df = pd.DataFrame(data)
    
    filtered = filter_cohort(
        df,
        min_age=65,
        required_covariates=['age', 'sex', 'bmi', 'fiber', 'antibiotics'],
        target_metrics=['shannon_diversity', 'cognitive_score'],
        impute_missing=True
    )
    
    # All BMI values should be non-null after imputation
    assert filtered['bmi'].notna().all()
    assert filtered.attrs.get('zero_variance_detected', False) == False

def test_filter_cohort_listwise_deletion():
    """Test filtering with listwise deletion for missing covariates."""
    n = 50
    data = {
        'participant_id': range(1, n + 1),
        'age': np.random.randint(65, 85, n),
        'sex': np.random.choice(['M', 'F'], n),
        'bmi': [np.nan] * 10 + list(np.random.normal(25, 4, 40)),  # Missing values
        'fiber': np.random.normal(20, 5, n),
        'antibiotics': np.random.choice([0, 1], n),
        'shannon_diversity': np.random.normal(3.5, 0.5, n),
        'cognitive_score': np.random.normal(85, 10, n)
    }
    df = pd.DataFrame(data)
    
    filtered = filter_cohort(
        df,
        min_age=65,
        required_covariates=['age', 'sex', 'bmi', 'fiber', 'antibiotics'],
        target_metrics=['shannon_diversity', 'cognitive_score'],
        impute_missing=False
    )
    
    # All BMI values should be non-null (listwise deletion)
    assert filtered['bmi'].notna().all()
    assert len(filtered) < len(df)  # Some rows should be removed
    assert filtered.attrs.get('zero_variance_detected', False) == False