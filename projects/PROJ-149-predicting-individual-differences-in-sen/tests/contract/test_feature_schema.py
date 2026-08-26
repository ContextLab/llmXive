import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import json
import sys
import os

# Add code directory to path if running from tests root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from config import get_path

def load_schema(schema_name):
    """Load a schema definition from the contracts directory."""
    schema_path = Path(os.path.join(os.path.dirname(__file__), '..', 'contracts', f'{schema_name}.schema.yaml'))
    if not schema_path.exists():
        # Create default schema if missing to allow test to define it
        return None
    import yaml
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def test_feature_schema_columns():
    """Validate that data/processed/features.csv has required columns."""
    features_path = get_path('processed', 'features.csv')
    if not os.path.exists(features_path):
        pytest.skip(f"File {features_path} not found. Run pipeline first.")
    
    df = pd.read_csv(features_path)
    
    required_cols = [
        'participant_id', 'median_rt', 
        'delta_rel', 'theta_rel', 'alpha_rel', 
        'low_beta_rel', 'high_beta_rel', 'gamma_rel'
    ]
    
    missing_cols = [col for col in required_cols if col not in df.columns]
    assert len(missing_cols) == 0, f"Missing columns: {missing_cols}"

def test_feature_schema_no_nulls():
    """Validate that data/processed/features.csv has no nulls in critical columns."""
    features_path = get_path('processed', 'features.csv')
    if not os.path.exists(features_path):
        pytest.skip(f"File {features_path} not found. Run pipeline first.")
    
    df = pd.read_csv(features_path)
    
    critical_cols = ['participant_id', 'median_rt', 'delta_rel', 'theta_rel', 
                    'alpha_rel', 'low_beta_rel', 'high_beta_rel', 'gamma_rel']
    
    for col in critical_cols:
        assert not df[col].isnull().any(), f"Column {col} contains null values"

def test_feature_schema_rt_range():
    """Validate that median_rt is within 100-2000 ms."""
    features_path = get_path('processed', 'features.csv')
    if not os.path.exists(features_path):
        pytest.skip(f"File {features_path} not found. Run pipeline first.")
    
    df = pd.read_csv(features_path)
    
    assert (df['median_rt'] >= 100).all(), "Found median_rt < 100 ms"
    assert (df['median_rt'] <= 2000).all(), "Found median_rt > 2000 ms"

def test_result_schema_model_results():
    """Validate model_results.json schema."""
    model_path = get_path('processed', 'model_results.json')
    if not os.path.exists(model_path):
        pytest.skip(f"File {model_path} not found. Run pipeline first.")
    
    with open(model_path, 'r') as f:
        data = json.load(f)
    
    required_keys = ['adjusted_r2', 'optimal_lambda', 'rmse', 'test_r2', 'test_rmse']
    missing_keys = [k for k in required_keys if k not in data]
    assert len(missing_keys) == 0, f"Missing keys in model_results.json: {missing_keys}"

def test_result_schema_correlations_corrected():
    """Validate correlations_corrected.csv schema."""
    corr_path = get_path('processed', 'correlations_corrected.csv')
    if not os.path.exists(corr_path):
        pytest.skip(f"File {corr_path} not found. Run pipeline first.")
    
    df = pd.read_csv(corr_path)
    
    required_cols = ['band', 'r_value', 'p_value', 'n', 'significant']
    missing_cols = [col for col in required_cols if col not in df.columns]
    assert len(missing_cols) == 0, f"Missing columns in correlations_corrected.csv: {missing_cols}"

def test_result_schema_non_linear_comparison():
    """Validate non_linear_comparison.json schema."""
    nl_path = get_path('processed', 'non_linear_comparison.json')
    if not os.path.exists(nl_path):
        pytest.skip(f"File {nl_path} not found. Run pipeline first.")
    
    with open(nl_path, 'r') as f:
        data = json.load(f)
    
    required_keys = ['linear_r2', 'polynomial_r2', 'f_statistic', 'p_value', 
                    'significant_at_0p05', 'interpretation']
    missing_keys = [k for k in required_keys if k not in data]
    assert len(missing_keys) == 0, f"Missing keys in non_linear_comparison.json: {missing_keys}"

def test_result_schema_permutation_results():
    """Validate permutation_results.json schema."""
    perm_path = get_path('processed', 'permutation_results.json')
    if not os.path.exists(perm_path):
        pytest.skip(f"File {perm_path} not found. Run pipeline first.")
    
    with open(perm_path, 'r') as f:
        data = json.load(f)
    
    required_keys = ['observed_r2', 'p_value', 'null_distribution_path']
    missing_keys = [k for k in required_keys if k not in data]
    assert len(missing_keys) == 0, f"Missing keys in permutation_results.json: {missing_keys}"
