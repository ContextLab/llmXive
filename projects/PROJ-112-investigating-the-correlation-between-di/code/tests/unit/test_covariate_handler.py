import pytest
import pandas as pd
import numpy as np
import json
import os
from pathlib import Path
import tempfile
import shutil

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
        'age': [25.0, 30.0, np.nan, 40.0, 50.0],
        'bmi': [22.0, np.nan, 24.0, 26.0, np.nan],
        'antibiotics': [0, 1, 0, np.nan, 1],
        'high_missing_col': [np.nan, np.nan, np.nan, np.nan, np.nan], # 100% missing
        'normal_col': [1, 2, 3, 4, 5]
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for file I/O tests."""
    tmp = tempfile.mkdtemp()
    yield tmp
    shutil.rmtree(tmp, ignore_errors=True)

def test_calculate_missing_ratio(sample_df):
    """Test calculation of missing ratios."""
    ratios = calculate_missing_ratio(sample_df)
    
    # age: 1/5 = 0.2
    assert ratios['age'] == 0.2
    # bmi: 2/5 = 0.4
    assert ratios['bmi'] == 0.4
    # antibiotics: 1/5 = 0.2
    assert ratios['antibiotics'] == 0.2
    # high_missing_col: 5/5 = 1.0
    assert ratios['high_missing_col'] == 1.0
    # normal_col: 0/5 = 0.0
    assert ratios['normal_col'] == 0.0

def test_exclude_high_missingness(sample_df):
    """Test exclusion of columns with >20% missing."""
    filtered_df, excluded = exclude_high_missingness(sample_df, threshold=0.20)
    
    # 'high_missing_col' (100%) should be excluded
    assert 'high_missing_col' in excluded
    assert 'high_missing_col' not in filtered_df.columns
    
    # 'bmi' (40%) should be excluded
    assert 'bmi' in excluded
    assert 'bmi' not in filtered_df.columns
    
    # Others should remain
    assert 'age' in filtered_df.columns
    assert 'antibiotics' in filtered_df.columns

def test_exclude_high_missingness_threshold_adjusted(sample_df):
    """Test exclusion with a higher threshold."""
    # Set threshold to 0.50 (50%)
    filtered_df, excluded = exclude_high_missingness(sample_df, threshold=0.50)
    
    # Only 'high_missing_col' (100%) should be excluded
    assert 'high_missing_col' in excluded
    assert 'bmi' not in excluded # 40% < 50%
    assert 'bmi' in filtered_df.columns

def test_impute_with_mice_no_missing():
    """Test imputation on data with no missing values."""
    df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
    result = impute_with_mice(df)
    pd.testing.assert_frame_equal(result, df)

def test_impute_with_mice_basic(sample_df):
    """Test basic MICE imputation functionality."""
    # Select columns that actually have missing data
    cols = ['age', 'bmi']
    result = impute_with_mice(sample_df, columns=cols)
    
    # Check that result has no NaN in specified columns
    assert not result['age'].isna().any()
    assert not result['bmi'].isna().any()
    
    # Check that original shape is preserved
    assert result.shape == sample_df.shape

def test_process_covariates_full_pipeline(sample_df):
    """Test the full covariate processing pipeline."""
    cols = ['age', 'bmi', 'antibiotics', 'high_missing_col']
    
    processed_df, summary = process_covariates(
        sample_df,
        covariate_columns=cols,
        missing_threshold=0.20,
        impute=True,
        num_iterations=2 # Fewer iterations for faster test
    )
    
    # Verify summary structure
    assert 'original_columns' in summary
    assert 'excluded_columns' in summary
    assert 'imputed_columns' in summary
    assert 'final_columns' in summary
    
    # Verify high_missing_col was excluded
    assert 'high_missing_col' in summary['excluded_columns']
    assert 'high_missing_col' not in processed_df.columns
    
    # Verify remaining columns have no missing values (due to imputation)
    for col in summary['final_columns']:
        assert not processed_df[col].isna().any()

def test_process_covariates_no_impute(sample_df):
    """Test pipeline with imputation disabled."""
    cols = ['age', 'bmi', 'antibiotics']
    
    processed_df, summary = process_covariates(
        sample_df,
        covariate_columns=cols,
        missing_threshold=0.50, # Higher threshold so nothing excluded
        impute=False
    )
    
    # Since impute=False, missing values should remain
    assert processed_df['age'].isna().any()
    assert processed_df['bmi'].isna().any()
    
    # Summary should reflect no imputation
    assert len(summary['imputed_columns']) == 0
