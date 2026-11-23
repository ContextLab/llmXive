import pytest
import pandas as pd
import numpy as np
import json
from pathlib import Path
import tempfile
import os

from src.models.fit import (
    fit_beta_regression,
    fit_gaussian_glm,
    fit_ridge_regression,
    save_model_metrics,
    load_schema,
    validate_against_schema,
    prepare_features_for_modeling
)

@pytest.fixture
def sample_data():
    np.random.seed(42)
    n = 100
    df = pd.DataFrame({
        'material_imbalance_move10': np.random.randn(n),
        'outcome_deviation': np.random.randn(n) * 0.5,
        'eco_code': np.random.choice(['A00', 'B20', 'C50', 'D30', 'E90'], n)
    })
    return df

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)

def test_fit_beta_regression(sample_data):
    X, y, _ = prepare_features_for_modeling(sample_data)
    result = fit_beta_regression(X, y)
    assert result['model_type'] == 'Beta'
    assert 'coefficients' in result
    assert 'r_squared' in result
    assert isinstance(result['r_squared'], float)

def test_fit_gaussian_glm(sample_data):
    X, y, _ = prepare_features_for_modeling(sample_data)
    result = fit_gaussian_glm(X, y)
    assert result['model_type'] == 'Gaussian GLM'
    assert 'coefficients' in result

def test_fit_ridge_regression(sample_data):
    X, y, _ = prepare_features_for_modeling(sample_data)
    result = fit_ridge_regression(X, y)
    assert result['model_type'] == 'Ridge'
    assert 'coefficients' in result

def test_save_model_metrics(temp_dir, sample_data):
    X, y, _ = prepare_features_for_modeling(sample_data)
    beta_res = fit_beta_regression(X, y)
    gauss_res = fit_gaussian_glm(X, y)
    ridge_res = fit_ridge_regression(X, y)
    
    fdr_results = pd.DataFrame({
        'original_p_value': [0.05, 0.01],
        'corrected_p_value': [0.06, 0.02]
    }, index=['material_imbalance_move10', 'const'])
    
    cv_scores = {
        'Beta': [0.1, 0.1, 0.1],
        'Gaussian GLM': [0.2, 0.2, 0.2],
        'Ridge': [0.2, 0.2, 0.2]
    }
    
    output_path = temp_dir / "model_metrics.json"
    schema_path = Path("specs/contracts/model_output.schema.yaml")
    
    # Create schema if it doesn't exist in test env
    if not schema_path.exists():
        schema_content = {
            "schema_name": "model_output",
            "version": "1.0",
            "columns": [
                {"name": "model_type", "type": "string", "required": True},
                {"name": "coefficients", "type": "object", "required": True},
                {"name": "p_values", "type": "object", "required": True},
                {"name": "r_squared", "type": "float", "required": True},
                {"name": "aic", "type": "float", "required": True},
                {"name": "cross_validation_scores", "type": "array", "required": True},
                {"name": "significant_predictors", "type": "array", "required": True}
            ]
        }
        import yaml
        with open(schema_path, 'w') as f:
            yaml.dump(schema_content, f)
    
    save_model_metrics(beta_res, gauss_res, ridge_res, fdr_results, cv_scores, output_path, schema_path)
    
    assert output_path.exists()
    with open(output_path, 'r') as f:
        data = json.load(f)
    
    assert len(data) == 3
    assert any(item['model_type'] == 'Beta' for item in data)
    assert any(item['model_type'] == 'Gaussian GLM' for item in data)
    assert any(item['model_type'] == 'Ridge' for item in data)
    
    # Check for significant predictors
    beta_item = next(item for item in data if item['model_type'] == 'Beta')
    assert 'significant_predictors' in beta_item
    assert isinstance(beta_item['significant_predictors'], list)