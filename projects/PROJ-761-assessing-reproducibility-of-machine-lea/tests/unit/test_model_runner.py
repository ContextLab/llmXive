import pytest
import numpy as np
from pathlib import Path
import json
import tempfile
import pandas as pd

from model_runner import (
    count_model_parameters,
    load_processed_data,
    encode_smiles,
    train_model,
    evaluate_model,
    run_sensitivity_analysis,
    run_reproducibility_assessment
)
from metrics import calculate_mae, calculate_r2, calculate_spearman_rho

def test_count_model_parameters():
    """Test parameter counting for a simple model."""
    from sklearn.linear_model import Ridge
    model = Ridge()
    # Simulate fitting
    X = np.random.rand(10, 5)
    y = np.random.rand(10)
    model.fit(X, y)
    params = count_model_parameters(model)
    assert params > 0, "Parameter count should be positive"

def test_encode_smiles():
    """Test SMILES encoding."""
    smiles = ["CCO", "CC", "O"]
    encoded = encode_smiles(smiles)
    assert encoded.shape == (3, 13), f"Expected (3, 13), got {encoded.shape}"
    assert isinstance(encoded, np.ndarray)

def test_train_model_within_limit():
    """Test training a model that stays within parameter limit."""
    X = np.random.rand(50, 13)
    y = np.random.rand(50)
    model, is_substituted = train_model(X, y, seed=42, max_params=1000000)
    assert model is not None
    assert not is_substituted, "Model should not be substituted"

def test_train_model_substitution():
    """Test that a model exceeding limit is substituted."""
    X = np.random.rand(50, 13)
    y = np.random.rand(50)
    # Force substitution with very low limit
    model, is_substituted = train_model(X, y, seed=42, max_params=10)
    assert is_substituted, "Model should be substituted due to low limit"

def test_evaluate_model():
    """Test model evaluation."""
    from sklearn.ensemble import RandomForestRegressor
    X = np.random.rand(100, 13)
    y = np.random.rand(100)
    
    model = RandomForestRegressor(random_state=42, n_estimators=5)
    model.fit(X, y)
    
    results = evaluate_model(model, X, y, {'mae': 0.5, 'r2': 0.8, 'spearman': 0.7})
    
    assert 'mae' in results
    assert 'r2' in results
    assert 'spearman' in results
    assert 'deviation_index' in results
    assert 'predictions' in results

def test_run_sensitivity_analysis():
    """Test sensitivity analysis."""
    X = np.random.rand(100, 13)
    y = np.random.rand(100)
    
    results = run_sensitivity_analysis(X, y, seeds=[42, 123])
    
    assert 'metric_std' in results
    assert 'max_metric_std' in results
    assert 'mae' in results['metric_std']
    assert 'r2' in results['metric_std']

def test_run_reproducibility_assessment(tmp_path):
    """Test full reproducibility assessment."""
    # Create dummy data
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    
    df = pd.DataFrame({
        'smiles': ['CCO', 'CC', 'O', 'C', 'N'],
        'yield': [0.8, 0.6, 0.9, 0.5, 0.7]
    })
    csv_path = data_dir / "test.csv"
    df.to_csv(csv_path, index=False)
    
    result = run_reproducibility_assessment(
        paper_id="test_paper",
        data_path=csv_path,
        reported_metrics={'mae': 0.5, 'r2': 0.8, 'spearman': 0.7},
        reported_seed=42
    )
    
    assert result['status'] == 'success'
    assert result['paper_id'] == 'test_paper'
    assert 'metrics' in result
    assert 'sensitivity_analysis' in result

def test_run_reproducibility_assessment_missing_data(tmp_path):
    """Test handling of missing data."""
    result = run_reproducibility_assessment(
        paper_id="missing_paper",
        data_path=Path("nonexistent.csv"),
        reported_metrics={'mae': 0.5},
        reported_seed=42
    )
    
    assert result['status'] == 'failed'
    assert result['reason'] == 'Data Unavailable'
