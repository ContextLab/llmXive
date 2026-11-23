"""
Unit tests for significance testing on reduced feature set (T026a).
"""
import pytest
import pandas as pd
import numpy as np
import json
import tempfile
import os
from pathlib import Path

from code.src.modeling.significance_test import (
    calculate_vif,
    remove_collinear_features,
    calculate_pvalues,
    run_significance_test_on_reduced_set
)


@pytest.fixture
def sample_reduced_data():
    """Create sample reduced feature set with no collinearity."""
    np.random.seed(42)
    n_samples = 100
    
    data = {
        'Tc': np.random.normal(39, 5, n_samples),
        'impurity_Al': np.random.normal(1, 0.5, n_samples),
        'impurity_C': np.random.normal(0.5, 0.3, n_samples),
        'impurity_Si': np.random.normal(0.2, 0.1, n_samples),
        'impurity_Fe': np.random.normal(0.1, 0.05, n_samples),
    }
    
    # Ensure low correlation between features
    return pd.DataFrame(data)


@pytest.fixture
def temp_reduced_csv(sample_reduced_data):
    """Save sample data to temp CSV."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        sample_reduced_data.to_csv(f.name, index=False)
        yield f.name
        os.unlink(f.name)


@pytest.fixture
def temp_output_json():
    """Create temp output path."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        output_path = f.name
    yield output_path
    if os.path.exists(output_path):
        os.unlink(output_path)


def test_calculate_vif_on_reduced_set(temp_reduced_csv):
    """Test VIF calculation on reduced feature set."""
    df = pd.read_csv(temp_reduced_csv)
    feature_cols = ['impurity_Al', 'impurity_C', 'impurity_Si', 'impurity_Fe']
    
    vif_df = calculate_vif(df, feature_cols)
    
    assert len(vif_df) == len(feature_cols)
    assert 'feature' in vif_df.columns
    assert 'VIF' in vif_df.columns
    
    # All VIF should be relatively low for reduced set
    assert all(vif_df['VIF'] < 10), "VIF should be low on reduced set"


def test_calculate_pvalues_on_reduced_set(temp_reduced_csv):
    """Test p-value calculation on reduced feature set."""
    df = pd.read_csv(temp_reduced_csv)
    feature_cols = ['impurity_Al', 'impurity_C', 'impurity_Si', 'impurity_Fe']
    
    pvalue_df = calculate_pvalues(df, 'Tc', feature_cols)
    
    assert len(pvalue_df) == len(feature_cols)
    assert 'feature' in pvalue_df.columns
    assert 'p_value' in pvalue_df.columns
    assert all(0 <= pvalue_df['p_value'])
    assert all(pvalue_df['p_value'] <= 1)


def test_run_significance_test_on_reduced_set(temp_reduced_csv, temp_output_json):
    """Test full significance test pipeline on reduced set."""
    results = run_significance_test_on_reduced_set(
        temp_reduced_csv,
        temp_output_json,
        target_col='Tc',
        vif_threshold=5.0,
        pvalue_threshold=0.05
    )
    
    # Check results structure
    assert 'total_features' in results
    assert 'significant_features' in results
    assert 'all_pvalues' in results
    assert 'vif_verification' in results
    
    # Check output file
    assert os.path.exists(temp_output_json)
    with open(temp_output_json, 'r') as f:
        loaded_results = json.load(f)
    
    assert loaded_results['total_features'] == results['total_features']
    assert loaded_results['significant_features'] == results['significant_features']


def test_significance_test_missing_input():
    """Test that missing input file raises error."""
    with pytest.raises(FileNotFoundError):
        run_significance_test_on_reduced_set(
            "nonexistent/path/reduced_feature_set.csv",
            "output/results.json"
        )


def test_significance_test_empty_features():
    """Test handling of dataset with no features."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        pd.DataFrame({'Tc': [1, 2, 3]}).to_csv(f.name, index=False)
        temp_path = f.name
    
    try:
        with pytest.raises(ValueError, match="No features found"):
            run_significance_test_on_reduced_set(
                temp_path,
                "output/results.json"
            )
    finally:
        os.unlink(temp_path)
