"""Tests for modeling pipeline."""
import json
import os
import tempfile
from pathlib import Path
import pytest
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor

from modeling import (
    load_features_and_target,
    apply_ilr_transformation,
    load_split_indices,
    train_random_forest_with_cv,
    run_repeated_cv,
    evaluate_model_on_test,
    save_model_metrics,
    save_residuals,
    check_mae_threshold,
    save_methodological_flags,
    save_model,
    run_modeling_pipeline
)

@pytest.fixture
def sample_data():
    """Create sample data for testing."""
    df = pd.DataFrame({
        'Cu': [0.05, 0.06, 0.04, 0.07, 0.05],
        'Mg': [0.03, 0.04, 0.02, 0.05, 0.03],
        'Si': [0.02, 0.03, 0.01, 0.04, 0.02],
        'Zn': [0.01, 0.02, 0.01, 0.03, 0.01],
        'Mn': [0.01, 0.01, 0.01, 0.02, 0.01],
        'poisson_ratio': [0.33, 0.34, 0.32, 0.35, 0.33]
    })
    return df

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

def test_ilr_transform_handles_zero_sum(sample_data):
    """Test that ILR transformation handles normal compositions."""
    result = apply_ilr_transformation(sample_data)
    assert 'ilr_0' in result.columns
    assert 'ilr_1' in result.columns
    assert 'ilr_2' in result.columns
    assert 'ilr_3' in result.columns
    assert 'ilr_4' in result.columns
    assert len(result) == len(sample_data)

def test_rf_training_converges(sample_data, temp_dir):
    """Test that RF training converges and produces a model."""
    # Prepare features
    ilr_data = apply_ilr_transformation(sample_data)
    X = ilr_data
    y = sample_data['poisson_ratio']
    
    model = train_random_forest_with_cv(X, y)
    assert isinstance(model, RandomForestRegressor)
    assert model.fitted_

def test_cv_split_reproducibility(sample_data):
    """Test that CV splits are reproducible with fixed random state."""
    ilr_data = apply_ilr_transformation(sample_data)
    X = ilr_data
    y = sample_data['poisson_ratio']
    
    result1 = run_repeated_cv(X, y, n_splits=5, n_repeats=2)
    result2 = run_repeated_cv(X, y, n_splits=5, n_repeats=2)
    
    # Results should be identical due to fixed random state in KFold
    assert result1['cv_mae'] == result2['cv_mae']

def test_mae_threshold_check():
    """Test MAE threshold logic."""
    assert check_mae_threshold(0.04) == False
    assert check_mae_threshold(0.05) == False
    assert check_mae_threshold(0.051) == True
    assert check_mae_threshold(0.10) == True

def test_save_methodological_flags(temp_dir):
    """Test saving methodological flags."""
    output_path = os.path.join(temp_dir, 'flags.json')
    save_methodological_flags(0.045, False, output_path)
    
    assert os.path.exists(output_path)
    with open(output_path, 'r') as f:
        data = json.load(f)
    
    assert 'mae_flag' in data
    assert 'cv_mae' in data
    assert data['mae_flag'] == False
    assert data['cv_mae'] == 0.045

def test_save_model_metrics(temp_dir):
    """Test saving model metrics."""
    output_path = os.path.join(temp_dir, 'metrics.json')
    metrics = {
        'cv_mae': 0.045,
        'cv_std': 0.005,
        'cv_ci_lower': 0.035,
        'cv_ci_upper': 0.055,
        'test_mae': 0.048
    }
    save_model_metrics(metrics, output_path)
    
    assert os.path.exists(output_path)
    with open(output_path, 'r') as f:
        data = json.load(f)
    
    assert data == metrics

def test_save_residuals(temp_dir):
    """Test saving residuals."""
    output_path = os.path.join(temp_dir, 'residuals.json')
    residuals = [0.01, -0.02, 0.005, -0.01, 0.015]
    save_residuals(residuals, output_path)
    
    assert os.path.exists(output_path)
    with open(output_path, 'r') as f:
        data = json.load(f)
    
    assert data == residuals

def test_save_model(temp_dir, sample_data):
    """Test saving trained model."""
    ilr_data = apply_ilr_transformation(sample_data)
    X = ilr_data
    y = sample_data['poisson_ratio']
    
    model = train_random_forest_with_cv(X, y)
    model_path = os.path.join(temp_dir, 'model.pkl')
    save_model(model, model_path)
    
    assert os.path.exists(model_path)
    
    # Verify it can be loaded
    loaded_model = joblib.load(model_path)
    assert isinstance(loaded_model, RandomForestRegressor)

def test_run_modeling_pipeline_end_to_end(temp_dir, sample_data):
    """Test full pipeline execution."""
    # Create necessary files
    data_path = os.path.join(temp_dir, 'alloys_clean.parquet')
    splits_path = os.path.join(temp_dir, 'split_indices.json')
    metrics_output = os.path.join(temp_dir, 'model_metrics.json')
    residuals_output = os.path.join(temp_dir, 'residuals.json')
    flags_output = os.path.join(temp_dir, 'methodological_flags.json')
    model_output = os.path.join(temp_dir, 'rf_model.pkl')
    
    # Save sample data
    sample_data.to_parquet(data_path)
    
    # Create split indices
    n = len(sample_data)
    train_idx = list(range(0, 3))
    val_idx = list(range(3, 4))
    test_idx = list(range(4, n))
    
    splits = {
        'train': train_idx,
        'val': val_idx,
        'test': test_idx
    }
    with open(splits_path, 'w') as f:
        json.dump(splits, f)
    
    # Run pipeline
    results = run_modeling_pipeline(
        data_path=data_path,
        splits_path=splits_path,
        metrics_output=metrics_output,
        residuals_output=residuals_output,
        flags_output=flags_output,
        model_output=model_output
    )
    
    # Verify outputs exist
    assert os.path.exists(metrics_output)
    assert os.path.exists(residuals_output)
    assert os.path.exists(flags_output)
    assert os.path.exists(model_output)
    
    # Verify results structure
    assert 'cv_mae' in results
    assert 'test_mae' in results
    assert 'mae_flag' in results
    assert isinstance(results['cv_mae'], float)
    assert isinstance(results['test_mae'], float)
    assert isinstance(results['mae_flag'], bool)