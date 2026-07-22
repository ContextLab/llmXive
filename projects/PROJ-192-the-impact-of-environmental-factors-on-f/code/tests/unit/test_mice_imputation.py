"""
Unit tests for MICE imputation functionality in preprocess.py.
"""
import os
import tempfile
import pandas as pd
import numpy as np
import pytest
from pathlib import Path

from src.pipelines.preprocess import (
    perform_mice_imputation,
    load_harmonized_metadata,
    save_cleaned_metadata,
    run_preprocessing_pipeline,
    identify_numeric_columns
)

@pytest.fixture
def sample_metadata_with_nans():
    """Create a sample metadata DataFrame with missing values."""
    data = {
        'sample_id': ['S1', 'S2', 'S3', 'S4', 'S5', 'S6', 'S7', 'S8', 'S9', 'S10', 'S11', 'S12'],
        'pH': [6.5, np.nan, 7.0, 6.8, np.nan, 7.2, 6.9, 7.1, np.nan, 6.7, 7.3, 6.6],
        'nutrients': [10.5, 12.0, np.nan, 11.5, 10.8, np.nan, 11.2, 12.5, 10.9, np.nan, 11.8, 10.2],
        'moisture': [0.25, 0.28, 0.22, np.nan, 0.26, 0.24, np.nan, 0.27, 0.23, 0.25, np.nan, 0.26],
        'biome': ['Forest', 'Forest', 'Grassland', 'Forest', 'Grassland', 'Forest', 'Grassland', 'Forest', 'Grassland', 'Forest', 'Grassland', 'Forest']
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_metadata_clean():
    """Create a sample metadata DataFrame without missing values."""
    data = {
        'sample_id': ['S1', 'S2', 'S3', 'S4', 'S5'],
        'pH': [6.5, 7.0, 6.8, 7.2, 6.9],
        'nutrients': [10.5, 12.0, 11.5, 10.8, 11.2],
        'moisture': [0.25, 0.28, 0.22, 0.26, 0.24],
        'biome': ['Forest', 'Forest', 'Grassland', 'Grassland', 'Forest']
    }
    return pd.DataFrame(data)

def test_identify_numeric_columns(sample_metadata_with_nans):
    """Test that numeric columns are correctly identified."""
    numeric_cols = identify_numeric_columns(sample_metadata_with_nans)
    assert 'pH' in numeric_cols
    assert 'nutrients' in numeric_cols
    assert 'moisture' in numeric_cols
    assert 'biome' not in numeric_cols
    assert 'sample_id' not in numeric_cols

def test_perform_mice_imputation_with_missing_values(sample_metadata_with_nans):
    """Test MICE imputation on data with missing values."""
    df_clean, converged = perform_mice_imputation(
        sample_metadata_with_nans,
        iterations=3,
        random_state=42
    )
    
    # Check that no NaNs remain in numeric columns
    numeric_cols = identify_numeric_columns(df_clean)
    assert df_clean[numeric_cols].isnull().sum().sum() == 0
    
    # Check that we still have a reasonable number of rows
    assert len(df_clean) >= len(sample_metadata_with_nans) - 2  # Allow for some row dropping

def test_perform_mice_imputation_no_missing_values(sample_metadata_clean):
    """Test that imputation skips when no missing values exist."""
    df_clean, converged = perform_mice_imputation(
        sample_metadata_clean,
        iterations=3,
        random_state=42
    )
    
    # Should return the same data unchanged
    assert df_clean.equals(sample_metadata_clean)
    assert converged is True

def test_perform_mice_imputation_insufficient_rows():
    """Test that imputation handles insufficient rows gracefully."""
    data = {
        'sample_id': ['S1', 'S2'],
        'pH': [6.5, np.nan],
        'nutrients': [10.5, 12.0]
    }
    df = pd.DataFrame(data)
    
    df_clean, converged = perform_mice_imputation(df, iterations=3, random_state=42)
    
    # Should return original data with warning (no imputation done)
    assert len(df_clean) == 2
    assert converged is True

def test_save_cleaned_metadata(tmp_path):
    """Test saving cleaned metadata to CSV."""
    data = {
        'sample_id': ['S1', 'S2', 'S3'],
        'pH': [6.5, 7.0, 6.8],
        'nutrients': [10.5, 12.0, 11.5]
    }
    df = pd.DataFrame(data)
    
    output_path = tmp_path / "cleaned_metadata.csv"
    save_cleaned_metadata(df, str(output_path))
    
    assert output_path.exists()
    
    # Verify contents
    loaded_df = pd.read_csv(output_path)
    assert len(loaded_df) == 3
    assert 'pH' in loaded_df.columns
    assert 'nutrients' in loaded_df.columns

def test_run_preprocessing_pipeline(tmp_path, sample_metadata_with_nans):
    """Test the full preprocessing pipeline."""
    input_path = tmp_path / "harmonized_matrix.csv"
    output_path = tmp_path / "cleaned_metadata.csv"
    
    # Save input data
    sample_metadata_with_nans.to_csv(input_path, index=False)
    
    # Run pipeline
    df_clean, converged = run_preprocessing_pipeline(
        str(input_path),
        str(output_path),
        iterations=3,
        random_state=42
    )
    
    # Verify output file exists
    assert output_path.exists()
    
    # Verify no NaNs in output
    numeric_cols = identify_numeric_columns(df_clean)
    assert df_clean[numeric_cols].isnull().sum().sum() == 0
    
    # Verify convergence flag
    assert isinstance(converged, bool)

def test_run_preprocessing_pipeline_creates_directory(tmp_path):
    """Test that pipeline creates output directory if it doesn't exist."""
    input_path = tmp_path / "input.csv"
    output_path = tmp_path / "subdir" / "cleaned_metadata.csv"
    
    # Create input file
    data = {
        'sample_id': ['S1', 'S2', 'S3', 'S4', 'S5', 'S6', 'S7', 'S8', 'S9', 'S10', 'S11', 'S12'],
        'pH': [6.5, 7.0, 6.8, 7.2, 6.9, 7.1, 6.7, 7.3, 6.6, 6.8, 7.0, 6.9],
        'nutrients': [10.5, 12.0, 11.5, 10.8, 11.2, 12.5, 10.9, 11.8, 10.2, 11.0, 12.1, 10.7]
    }
    pd.DataFrame(data).to_csv(input_path, index=False)
    
    # Run pipeline - should create subdir
    run_preprocessing_pipeline(str(input_path), str(output_path), iterations=3)
    
    assert output_path.exists()

def test_mice_imputation_deterministic_with_seed(sample_metadata_with_nans):
    """Test that imputation is deterministic with fixed random state."""
    df1, _ = perform_mice_imputation(sample_metadata_with_nans, iterations=3, random_state=42)
    df2, _ = perform_mice_imputation(sample_metadata_with_nans, iterations=3, random_state=42)
    
    # Results should be identical with same seed
    pd.testing.assert_frame_equal(df1.reset_index(drop=True), df2.reset_index(drop=True))
