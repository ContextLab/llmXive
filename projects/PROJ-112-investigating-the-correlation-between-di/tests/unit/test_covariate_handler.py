import pytest
import pandas as pd
import numpy as np
import json
import os
from pathlib import Path
import tempfile
from src.preprocessing.covariate_handler import (
    calculate_missing_ratio, 
    exclude_high_missingness, 
    impute_with_mice, 
    process_covariates
)
from src.utils.logger import get_logger, reset_logger_cache

@pytest.fixture
def sample_df():
    """Create a sample DataFrame with missing values."""
    data = {
        'A': [1.0, 2.0, np.nan, 4.0, 5.0],
        'B': [10.0, np.nan, 30.0, 40.0, 50.0],
        'C': [100.0, 200.0, 300.0, 400.0, 500.0],  # No missing
        'D': [np.nan, np.nan, np.nan, np.nan, np.nan],  # All missing (>20%)
        'E': [1.0, 2.0, 3.0, 4.0, 5.0]
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

def test_calculate_missing_ratio(sample_df):
    """Test missing ratio calculation."""
    ratios = calculate_missing_ratio(sample_df)
    assert ratios['A'] == 0.2
    assert ratios['B'] == 0.2
    assert ratios['C'] == 0.0
    assert ratios['D'] == 1.0
    assert ratios['E'] == 0.0

def test_exclude_high_missingness(sample_df):
    """Test exclusion of columns with high missingness."""
    df_filtered, excluded = exclude_high_missingness(sample_df, threshold=0.20)
    assert 'D' in excluded
    assert 'A' not in excluded  # Exactly 20% is not > 20%
    assert 'B' not in excluded
    assert 'C' in df_filtered.columns
    assert 'D' not in df_filtered.columns

def test_exclude_high_missingness_threshold_adjusted(sample_df):
    """Test exclusion with a lower threshold."""
    df_filtered, excluded = exclude_high_missingness(sample_df, threshold=0.10)
    assert 'A' in excluded
    assert 'B' in excluded
    assert 'D' in excluded

def test_impute_with_mice_no_missing(sample_df):
    """Test MICE when no missing values exist in selected columns."""
    # Select only column C which has no missing values
    df_subset = sample_df[['C']].copy()
    df_imputed = impute_with_mice(df_subset)
    assert df_imputed.equals(df_subset)

def test_impute_with_mice_basic(sample_df):
    """Test basic MICE imputation."""
    df_subset = sample_df[['A', 'B', 'C']].copy()
    df_imputed = impute_with_mice(df_subset, iterations=2, seed=42)
    
    # Check no NaNs remain in the selected columns
    assert not df_imputed['A'].isna().any()
    assert not df_imputed['B'].isna().any()
    assert not df_imputed['C'].isna().any()
    
    # Check that imputed values are reasonable (not extreme)
    assert df_imputed['A'].min() >= 1.0
    assert df_imputed['A'].max() <= 5.0

def test_process_covariates_full_pipeline(sample_df):
    """Test the full covariate processing pipeline."""
    covariates = ['A', 'B', 'C', 'D', 'E']
    df_processed, metadata = process_covariates(
        sample_df, 
        covariates, 
        missing_threshold=0.20, 
        impute_iterations=2
    )
    
    # Check metadata
    assert metadata['original_columns'] == 5
    assert 'D' in metadata['excluded_columns']
    assert 'A' in df_processed.columns
    assert 'B' in df_processed.columns
    assert 'C' in df_processed.columns
    assert 'D' not in df_processed.columns
    
    # Check no missing values remain in processed columns
    assert not df_processed['A'].isna().any()
    assert not df_processed['B'].isna().any()
    
    # Check logger configuration
    logger = get_logger("test_covariate_handler")
    assert logger is not None
    assert len(logger.handlers) > 0

def test_process_covariates_no_impute(sample_df):
    """Test pipeline when no imputation is needed."""
    df_clean = sample_df[['C', 'E']].copy()
    covariates = ['C', 'E']
    df_processed, metadata = process_covariates(
        df_clean, 
        covariates, 
        missing_threshold=0.20
    )
    
    assert df_processed.equals(df_clean)
    assert metadata['imputed_columns'] == []
