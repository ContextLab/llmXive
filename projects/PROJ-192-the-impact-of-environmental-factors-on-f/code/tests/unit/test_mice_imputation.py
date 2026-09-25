import os
import tempfile
import pandas as pd
import numpy as np
import pytest
from pathlib import Path
from src.pipelines.preprocess import (
    identify_numeric_columns,
    perform_mice_imputation,
    save_cleaned_metadata,
    run_preprocessing_pipeline,
    impute_and_clean
)
import miceforest as mf

@pytest.fixture
def sample_metadata_with_nans():
    """Create a sample dataframe with missing values."""
    data = {
        'sample_id': ['S1', 'S2', 'S3', 'S4', 'S5'],
        'pH': [6.5, None, 7.2, 6.8, 7.0],
        'nutrients': [10.0, 12.5, None, 11.0, 13.0],
        'moisture': [20.0, 22.0, 19.5, None, 21.0],
        'category': ['A', 'B', 'A', 'B', 'A']
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_metadata_clean():
    """Create a sample dataframe without missing values."""
    data = {
        'sample_id': ['S1', 'S2', 'S3'],
        'pH': [6.5, 7.2, 6.8],
        'nutrients': [10.0, 12.5, 11.0],
        'moisture': [20.0, 22.0, 19.5],
        'category': ['A', 'B', 'A']
    }
    return pd.DataFrame(data)

def test_identify_numeric_columns(sample_metadata_with_nans):
    """Test that numeric columns are correctly identified."""
    cols = identify_numeric_columns(sample_metadata_with_nans)
    assert 'pH' in cols
    assert 'nutrients' in cols
    assert 'moisture' in cols
    assert 'category' not in cols
    assert 'sample_id' not in cols

def test_perform_mice_imputation_with_missing_values(sample_metadata_with_nans):
    """Test MICE imputation on data with missing values."""
    numeric_cols = identify_numeric_columns(sample_metadata_with_nans)
    result_df, converged = perform_mice_imputation(
        sample_metadata_with_nans,
        numeric_cols,
        max_iterations=3,
        seed=42
    )
    
    assert result_df is not None
    assert len(result_df) == len(sample_metadata_with_nans)
    # Check that imputed columns have no NaNs
    assert result_df['pH'].isnull().sum() == 0
    assert result_df['nutrients'].isnull().sum() == 0
    assert result_df['moisture'].isnull().sum() == 0
    assert converged is True

def test_perform_mice_imputation_no_missing_values(sample_metadata_clean):
    """Test that imputation skips when no missing values exist."""
    numeric_cols = identify_numeric_columns(sample_metadata_clean)
    result_df, converged = perform_mice_imputation(
        sample_metadata_clean,
        numeric_cols,
        max_iterations=3,
        seed=42
    )
    
    # Should return original data unchanged
    pd.testing.assert_frame_equal(result_df, sample_metadata_clean)
    assert converged is True

def test_perform_mice_imputation_insufficient_rows():
    """Test behavior with insufficient rows for MICE (needs > 2 rows usually)."""
    data = {
        'sample_id': ['S1'],
        'pH': [6.5],
        'nutrients': [10.0]
    }
    df = pd.DataFrame(data)
    numeric_cols = ['pH', 'nutrients']
    
    # Should handle gracefully or raise specific error
    # miceforest typically requires more rows to learn the model
    with pytest.raises((ValueError, Exception)):
        perform_mice_imputation(df, numeric_cols, max_iterations=3, seed=42)

def test_save_cleaned_metadata(sample_metadata_with_nans):
    """Test saving cleaned metadata to a temporary file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "cleaned_metadata.csv")
        # First impute to ensure no NaNs
        numeric_cols = identify_numeric_columns(sample_metadata_with_nans)
        imputed_df, _ = perform_mice_imputation(sample_metadata_with_nans, numeric_cols, max_iterations=3)
        
        result_path = save_cleaned_metadata(imputed_df, output_path)
        
        assert os.path.exists(result_path)
        saved_df = pd.read_csv(result_path)
        assert saved_df.isnull().sum().sum() == 0
        assert len(saved_df) == len(sample_metadata_with_nans)

def test_run_preprocessing_pipeline(sample_metadata_with_nans):
    """Test the full preprocessing pipeline."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "input.csv")
        output_path = os.path.join(tmpdir, "output.csv")
        
        # Save input
        sample_metadata_with_nans.to_csv(input_path, index=False)
        
        # Run pipeline
        result_path = run_preprocessing_pipeline(input_path, output_path, max_iterations=3)
        
        assert os.path.exists(result_path)
        result_df = pd.read_csv(result_path)
        assert result_df.isnull().sum().sum() == 0

def test_run_preprocessing_pipeline_creates_directory():
    """Test that the pipeline creates the output directory if it doesn't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "input.csv")
        output_dir = os.path.join(tmpdir, "subdir", "output.csv")
        
        data = {'pH': [6.5, None], 'val': [1.0, 2.0]}
        pd.DataFrame(data).to_csv(input_path, index=False)
        
        result_path = run_preprocessing_pipeline(input_path, output_dir, max_iterations=3)
        assert os.path.exists(result_path)

def test_mice_imputation_deterministic_with_seed(sample_metadata_with_nans):
    """Test that imputation is deterministic with a fixed seed."""
    numeric_cols = identify_numeric_columns(sample_metadata_with_nans)
    
    result1, _ = perform_mice_imputation(sample_metadata_with_nans, numeric_cols, max_iterations=3, seed=42)
    result2, _ = perform_mice_imputation(sample_metadata_with_nans, numeric_cols, max_iterations=3, seed=42)
    
    pd.testing.assert_frame_equal(result1, result2)