"""
Unit tests for the filtering module (T013).

Tests cover:
- Age filtering (>= 65)
- Non-null score filtering
- Covariate handling (listwise deletion and mean imputation)
- Zero-variance detection
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

from code.src.data.filtering import (
    filter_cohort,
    _filter_age,
    _filter_non_null_scores,
    _filter_covariates,
    _check_zero_variance,
    MIN_AGE,
    REQUIRED_COVARIATES,
    REQUIRED_SCORES
)


@pytest.fixture
def sample_cohort_data():
    """Create a sample cohort DataFrame for testing."""
    np.random.seed(42)
    n = 100
    
    data = {
        'participant_id': [f'P{i:03d}' for i in range(n)],
        'age': np.random.randint(50, 85, n),
        'sex': np.random.choice(['M', 'F'], n),
        'bmi': np.random.normal(27, 4, n),
        'fiber': np.random.normal(20, 5, n),
        'antibiotics': np.random.choice([0, 1], n),
        'shannon': np.random.normal(3.5, 0.8, n),
        'cognitive_score': np.random.normal(85, 10, n)
    }
    
    # Introduce some missing values
    data['shannon'][np.random.choice(n, 5, replace=False)] = np.nan
    data['cognitive_score'][np.random.choice(n, 3, replace=False)] = np.nan
    data['bmi'][np.random.choice(n, 2, replace=False)] = np.nan
    
    return pd.DataFrame(data)


@pytest.fixture
def temp_input_file(sample_cohort_data):
    """Create a temporary input CSV file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        sample_cohort_data.to_csv(f, index=False)
        temp_path = Path(f.name)
    yield temp_path
    os.unlink(temp_path)


@pytest.fixture
def temp_output_file():
    """Create a temporary output file path."""
    with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as f:
        temp_path = Path(f.name)
    os.unlink(temp_path)
    yield temp_path


def test_filter_age(sample_cohort_data):
    """Test that age filtering correctly excludes participants < 65."""
    filtered = _filter_age(sample_cohort_data)
    
    # All ages should be >= 65
    assert filtered['age'].min() >= MIN_AGE
    
    # Check that some were filtered out (given our random distribution)
    assert len(filtered) < len(sample_cohort_data)


def test_filter_non_null_scores(sample_cohort_data):
    """Test that rows with missing scores are excluded."""
    initial_missing_shannon = sample_cohort_data['shannon'].isna().sum()
    initial_missing_cognitive = sample_cohort_data['cognitive_score'].isna().sum()
    
    filtered = _filter_non_null_scores(sample_cohort_data)
    
    # No missing scores should remain
    assert filtered['shannon'].isna().sum() == 0
    assert filtered['cognitive_score'].isna().sum() == 0
    
    # Should have removed at least the rows with missing values
    assert len(filtered) <= len(sample_cohort_data) - max(initial_missing_shannon, initial_missing_cognitive)


def test_filter_covariates_listwise(sample_cohort_data):
    """Test listwise deletion of missing covariates."""
    initial_missing = sample_cohort_data['bmi'].isna().sum()
    
    filtered = _filter_covariates(sample_cohort_data, impute_missing=False)
    
    # No missing covariates should remain
    for col in REQUIRED_COVARIATES:
        assert filtered[col].isna().sum() == 0
    
    # Should have removed rows with missing covariates
    assert len(filtered) < len(sample_cohort_data)


def test_filter_covariates_imputation(sample_cohort_data):
    """Test mean imputation for missing covariates."""
    initial_missing = sample_cohort_data['bmi'].isna().sum()
    
    filtered = _filter_covariates(sample_cohort_data, impute_missing=True)
    
    # No missing covariates should remain
    for col in REQUIRED_COVARIATES:
        assert filtered[col].isna().sum() == 0
    
    # Should retain all rows (no deletion)
    assert len(filtered) == len(sample_cohort_data)
    
    # Imputed values should be the mean
    original_mean = sample_cohort_data['bmi'].mean()
    imputed_values = filtered.loc[sample_cohort_data['bmi'].isna(), 'bmi']
    if len(imputed_values) > 0:
        assert all(imputed_values == original_mean)


def test_check_zero_variance():
    """Test zero-variance detection."""
    # Create data with a zero-variance column
    data = pd.DataFrame({
        'id': [1, 2, 3],
        'constant_col': [5, 5, 5],
        'variable_col': [1, 2, 3]
    })
    
    has_zero_var, zero_var_cols = _check_zero_variance(data)
    
    assert has_zero_var is True
    assert 'constant_col' in zero_var_cols
    assert 'variable_col' not in zero_var_cols


def test_check_no_zero_variance(sample_cohort_data):
    """Test that normally variable data has no zero-variance columns."""
    has_zero_var, zero_var_cols = _check_zero_variance(sample_cohort_data)
    
    # With random data, we shouldn't have zero variance
    assert has_zero_var is False
    assert len(zero_var_cols) == 0


def test_filter_cohort_integration(temp_input_file, temp_output_file):
    """Integration test for the full filtering pipeline."""
    stats = filter_cohort(
        input_path=temp_input_file,
        output_path=temp_output_file,
        impute_missing_covariates=False
    )
    
    # Verify output file exists
    assert temp_output_file.exists()
    
    # Load and verify output
    output_df = pd.read_csv(temp_output_file)
    
    # Verify constraints
    assert output_df['age'].min() >= MIN_AGE
    assert output_df['shannon'].isna().sum() == 0
    assert output_df['cognitive_score'].isna().sum() == 0
    
    for col in REQUIRED_COVARIATES:
        assert output_df[col].isna().sum() == 0
    
    # Verify stats
    assert stats['final_count'] == len(output_df)
    assert stats['final_count'] <= stats['initial_count']
    assert 'zero_variance_columns' in stats
    assert 'imputation_used' in stats


def test_filter_cohort_with_imputation(temp_input_file, temp_output_file):
    """Test filtering with mean imputation."""
    stats = filter_cohort(
        input_path=temp_input_file,
        output_path=temp_output_file,
        impute_missing_covariates=True
    )
    
    assert stats['imputation_used'] is True
    assert stats['final_count'] <= stats['initial_count']
    
    output_df = pd.read_csv(temp_output_file)
    for col in REQUIRED_COVARIATES:
        assert output_df[col].isna().sum() == 0