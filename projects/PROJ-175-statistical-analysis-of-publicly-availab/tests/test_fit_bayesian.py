import os
import json
import pytest
from pathlib import Path
import pandas as pd
import numpy as np

# Import the module functions
from code.models.fit_bayesian import (
    load_processed_data,
    prepare_features,
    fit_bayesian_model,
    save_results,
    save_convergence_log
)

@pytest.fixture
def mock_train_data(tmp_path):
    """Creates a mock train_set.parquet for testing"""
    data = {
        'compatibility_label': np.random.randint(0, 2, 100),
        'log_co_occurrence': np.random.randn(100),
        'similarity_score': np.random.rand(100),
        'functional_role_tertile': np.random.randint(0, 3, 100)
    }
    df = pd.DataFrame(data)
    output_path = tmp_path / "train_set.parquet"
    df.to_parquet(output_path)
    return str(output_path)

def test_prepare_features(mock_train_data, tmp_path):
    """Tests that features are prepared correctly"""
    # Temporarily move the mock file to the expected location
    expected_path = Path("data/processed/train_set.parquet")
    expected_path.parent.mkdir(parents=True, exist_ok=True)
    os.rename(mock_train_data, str(expected_path))
    
    try:
        df = pd.read_parquet(expected_path)
        X, y = prepare_features(df)
        
        assert X.shape[0] == df.shape[0]
        assert y.shape[0] == df.shape[0]
        # 2 continuous + 3 dummies (assuming 3 categories)
        assert X.shape[1] == 5 
    finally:
        # Cleanup
        if expected_path.exists():
            expected_path.unlink()

def test_save_results(tmp_path):
    """Tests that results are saved correctly"""
    results = {
        "status": "SUCCESS",
        "convergence": {"R_hat_max": 1.001, "ESS_min": 500},
        "coefficients": [{"var_names": "beta", "mean": 0.5}]
    }
    output_path = tmp_path / "test_results.json"
    
    save_results(results, str(output_path))
    
    assert output_path.exists()
    with open(output_path) as f:
        loaded = json.load(f)
    
    assert loaded['status'] == "SUCCESS"
    assert 'R_hat_max' in loaded['convergence']
