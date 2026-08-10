import pytest
import pandas as pd
import numpy as np
import os
import tempfile
from pathlib import Path

from src.preprocess.imputation import apply_imputation, run_imputation_pipeline
from src.exceptions import InsufficientDataError

@pytest.fixture
def sample_dataframe():
    """Creates a sample dataframe with missing values in predictors."""
    data = {
        'experiment_id': [1, 2, 3, 4, 5],
        'source': ['MP', 'NIST', 'arXiv', 'MP', 'NIST'],
        'source_id': ['MP-1', 'NIST-1', 'arXiv-1', 'MP-2', 'NIST-2'],
        'material_type': ['Al', 'Cu', 'Al', None, 'Cu'], # Missing material_type
        'milling_speed': [100.0, 200.0, None, 400.0, 500.0], # Missing milling_speed
        'milling_time': [1.0, None, 3.0, 4.0, 5.0], # Missing milling_time
        'ball_to_powder_ratio': [10.0, 20.0, 30.0, None, 50.0], # Missing ratio
        'youngs_modulus': [70.0, 110.0, 70.0, 110.0, None], # Missing youngs
        'density': [2.7, 8.9, 2.7, 8.9, 8.9],
        'process_duration': [10.0, 20.0, None, 40.0, 50.0], # Missing duration
        'd10': [10.0, 20.0, 30.0, 40.0, 50.0],
        'd50': [20.0, 30.0, 40.0, 50.0, 60.0],
        'd90': [30.0, 40.0, 50.0, 60.0, 70.0]
    }
    return pd.DataFrame(data)

def test_apply_imputation_no_missing(sample_dataframe):
    """Test imputation on a dataframe with no missing values."""
    df_clean = sample_dataframe.copy()
    df_clean['milling_speed'] = [100.0, 200.0, 300.0, 400.0, 500.0]
    df_clean['material_type'] = ['Al', 'Cu', 'Al', 'Cu', 'Cu']
    
    result = apply_imputation(df_clean)
    
    # Check that no nulls exist in predictors
    assert result.isna().sum().sum() == 0
    # Check that values are preserved (approximate for float comparison if needed, 
    # but here we just check no change in non-nulls if we didn't impute)
    # Since IterativeImputer might slightly alter values even if no missing, 
    # we focus on the null check.
    assert result['milling_speed'].equals(df_clean['milling_speed'])

def test_apply_imputation_with_missing(sample_dataframe):
    """Test imputation on a dataframe with missing values."""
    result = apply_imputation(sample_dataframe)
    
    # Check that no nulls exist in predictor columns
    predictor_cols = ['milling_speed', 'milling_time', 'ball_to_powder_ratio', 
                      'youngs_modulus', 'density', 'process_duration', 'material_type']
    for col in predictor_cols:
        assert not result[col].isna().any(), f"Column {col} still has missing values."
    
    # Check that target columns are preserved (not imputed by this function logic)
    # Note: The function doesn't touch targets, but if they were NaN, they remain NaN.
    # In this test data, targets are not NaN.
    assert result['d50'].equals(sample_dataframe['d50'])

def test_apply_imputation_empty_dataframe():
    """Test imputation on an empty dataframe."""
    df_empty = pd.DataFrame(columns=['milling_speed', 'd10'])
    with pytest.raises(InsufficientDataError):
        apply_imputation(df_empty)

def test_apply_imputation_missing_predictors(sample_dataframe):
    """Test imputation when predictor columns are missing from dataframe."""
    df_missing_pred = sample_dataframe[['d10', 'd50', 'd90']]
    with pytest.raises(InsufficientDataError):
        apply_imputation(df_missing_pred)

def test_run_imputation_pipeline(tmp_path):
    """Test the full pipeline with file I/O."""
    input_path = tmp_path / "input.parquet"
    output_path = tmp_path / "output.parquet"
    
    data = {
        'material_type': ['Al', 'Cu', None],
        'milling_speed': [100.0, None, 300.0],
        'milling_time': [1.0, 2.0, 3.0],
        'ball_to_powder_ratio': [10.0, 20.0, 30.0],
        'youngs_modulus': [70.0, 110.0, 70.0],
        'density': [2.7, 8.9, 2.7],
        'process_duration': [10.0, 20.0, 30.0],
        'd10': [10.0, 20.0, 30.0],
        'd50': [20.0, 30.0, 40.0],
        'd90': [30.0, 40.0, 50.0]
    }
    df = pd.DataFrame(data)
    df.to_parquet(input_path)
    
    run_imputation_pipeline(str(input_path), str(output_path))
    
    assert output_path.exists()
    result_df = pd.read_parquet(output_path)
    
    # Check no nulls in predictors
    predictor_cols = ['milling_speed', 'milling_time', 'ball_to_powder_ratio', 
                      'youngs_modulus', 'density', 'process_duration', 'material_type']
    for col in predictor_cols:
        assert not result_df[col].isna().any(), f"Column {col} still has missing values."