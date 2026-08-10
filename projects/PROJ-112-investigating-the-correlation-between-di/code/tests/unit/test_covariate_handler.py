import pytest
import pandas as pd
import numpy as np
import json
import os
from pathlib import Path
from src.preprocessing.covariate_handler import (
    calculate_missing_ratio,
    exclude_high_missingness,
    impute_with_mice,
    process_covariates
)

@pytest.fixture
def sample_df():
    """Create a sample DataFrame with missing values."""
    data = {
        'id': [1, 2, 3, 4, 5],
        'age': [25, np.nan, 30, 35, 40],
        'bmi': [22.5, 24.0, np.nan, 26.5, 28.0],
        'antibiotic_use': [0, 1, np.nan, 0, 1],
        'high_missing': [np.nan, np.nan, np.nan, 1, 0],  # 60% missing
        'fiber': [15, 20, 25, 30, 35]
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_dir(tmp_path):
    """Provide a temporary directory for output files."""
    return tmp_path

def test_calculate_missing_ratio(sample_df):
    """Test missing ratio calculation."""
    ratios = calculate_missing_ratio(sample_df, columns=['age', 'bmi', 'high_missing'])
    
    assert 'age' in ratios
    assert abs(ratios['age'] - 0.2) < 0.01  # 1/5
    assert abs(ratios['bmi'] - 0.2) < 0.01  # 1/5
    assert abs(ratios['high_missing'] - 0.6) < 0.01  # 3/5
    
    # Non-missing columns should have 0.0
    ratios_all = calculate_missing_ratio(sample_df)
    assert abs(ratios_all['fiber'] - 0.0) < 0.01

def test_exclude_high_missingness(sample_df):
    """Test exclusion of high missingness columns."""
    df_clean, excluded = exclude_high_missingness(sample_df, threshold=0.20)
    
    assert 'high_missing' not in df_clean.columns
    assert 'high_missing' in excluded
    assert 'age' in df_clean.columns
    assert 'bmi' in df_clean.columns
    assert len(excluded) == 1

def test_exclude_high_missingness_threshold_adjusted(sample_df):
    """Test exclusion with a different threshold."""
    # If threshold is 0.5, high_missing (0.6) is excluded, but age/bmi (0.2) are kept
    df_clean, excluded = exclude_high_missingness(sample_df, threshold=0.5)
    assert 'high_missing' not in df_clean.columns
    assert len(excluded) == 1
    
    # If threshold is 0.1, age and bmi should also be excluded
    df_clean_low, excluded_low = exclude_high_missingness(sample_df, threshold=0.1)
    assert 'age' not in df_clean_low.columns
    assert 'bmi' not in df_clean_low.columns
    assert len(excluded_low) == 3

def test_impute_with_mice_no_missing():
    """Test imputation when no missing values exist."""
    df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
    result, kernel = impute_with_mice(df)
    
    pd.testing.assert_frame_equal(result, df)
    assert kernel is None

def test_impute_with_mice_basic(sample_df):
    """Test basic MICE imputation."""
    # Select only numeric columns with missing values
    cols_to_impute = ['age', 'bmi', 'antibiotic_use']
    df_subset = sample_df[cols_to_impute]
    
    result, kernel = impute_with_mice(df_subset, iterations=2, random_state=42)
    
    # Check that no NaNs remain in the selected columns
    assert result.isna().sum().sum() == 0
    assert len(result) == len(df_subset)
    
    # Check that kernel is returned
    assert kernel is not None

def test_process_covariates_full_pipeline(sample_df, temp_dir):
    """Test the full covariate processing pipeline."""
    output_path = temp_dir / "processed_covariates.csv"
    covariate_cols = ['age', 'bmi', 'antibiotic_use', 'high_missing']
    
    result_df = process_covariates(
        sample_df,
        covariate_cols=covariate_cols,
        missing_threshold=0.20,
        impute=True,
        output_path=output_path
    )
    
    # Check file was created
    assert output_path.exists()
    
    # Check high_missing was excluded
    assert 'high_missing' not in result_df.columns
    
    # Check that other columns are imputed (no NaNs)
    for col in ['age', 'bmi', 'antibiotic_use']:
        if col in result_df.columns:
            assert result_df[col].isna().sum() == 0
    
    # Check id and fiber are untouched
    assert 'id' in result_df.columns
    assert 'fiber' in result_df.columns

def test_process_covariates_no_impute(sample_df, temp_dir):
    """Test pipeline with imputation disabled."""
    output_path = temp_dir / "no_impute.csv"
    covariate_cols = ['age', 'bmi']
    
    result_df = process_covariates(
        sample_df,
        covariate_cols=covariate_cols,
        missing_threshold=0.20,
        impute=False,
        output_path=output_path
    )
    
    # Missing values should remain if below threshold
    assert result_df['age'].isna().sum() > 0
    assert result_df['bmi'].isna().sum() > 0
    assert output_path.exists()