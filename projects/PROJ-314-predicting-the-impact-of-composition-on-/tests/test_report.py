"""
Unit tests for the report module, specifically T039: calculate_cv_stability.
"""
import pytest
import pandas as pd
import numpy as np
import json
from pathlib import Path
import sys
import os

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.report import calculate_cv_stability

def test_calculate_cv_stability_with_fold_data():
    """
    Test calculate_cv_stability when fold-level data is present in the DataFrame.
    Simulates the state after T036 has produced fold-specific columns.
    """
    # Create a mock DataFrame with fold-specific SHAP values
    # Features: 'mean_atomic_radius', 'electronegativity_std'
    data = {
        'weibull_modulus': [1.0, 2.0, 3.0],
        'mean_atomic_radius': [10.0, 11.0, 12.0],
        'electronegativity_std': [0.5, 0.6, 0.7],
        'shap_fold_mean_atomic_radius': [0.1, 0.2, 0.3],
        'shap_fold_electronegativity_std': [0.05, 0.06, 0.07]
    }
    df = pd.DataFrame(data)
    
    result = calculate_cv_stability(df, feature_columns=['mean_atomic_radius', 'electronegativity_std'])
    
    assert result['status'] == 'completed', f"Expected status 'completed', got {result['status']}"
    assert 'top_features' in result
    assert len(result['top_features']) > 0
    
    # Check that CV is calculated (std / mean)
    for feature in result['top_features']:
        assert 'coefficient_of_variation' in feature
        assert 'mean_importance' in feature
        assert 'std_importance' in feature

def test_calculate_cv_stability_missing_data():
    """
    Test calculate_cv_stability when no fold-level data is available.
    Should return a status indicating incomplete data.
    """
    # Create a DataFrame without fold columns
    data = {
        'weibull_modulus': [1.0, 2.0],
        'mean_atomic_radius': [10.0, 11.0],
    }
    df = pd.DataFrame(data)
    
    # Mock the file system to ensure no external file is found
    # (The function checks for shap_fold_importances.json)
    # We assume the file doesn't exist in the test environment.
    
    result = calculate_cv_stability(df, feature_columns=['mean_atomic_radius'])
    
    # Depending on implementation, it might return 'incomplete' or 'failed'
    # The key is that it does NOT crash and reports the issue.
    assert result['status'] in ['incomplete', 'failed'], f"Expected 'incomplete' or 'failed', got {result['status']}"
    assert 'reason' in result

def test_calculate_cv_stability_from_json_file():
    """
    Test calculate_cv_stability when data is loaded from shap_fold_importances.json.
    """
    import tempfile
    
    # Create a temporary file to simulate the artifact
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({
            'mean_atomic_radius': [0.1, 0.2, 0.3, 0.4, 0.5],
            'electronegativity_std': [0.01, 0.02, 0.03, 0.04, 0.05]
        }, f)
        temp_path = f.name
    
    try:
        # Rename to expected path temporarily
        expected_path = Path("data/results/shap_fold_importances.json")
        expected_path.parent.mkdir(parents=True, exist_ok=True)
        Path(temp_path).rename(expected_path)
        
        df = pd.DataFrame({'weibull_modulus': [1.0]})
        
        result = calculate_cv_stability(df, feature_columns=['mean_atomic_radius', 'electronegativity_std'])
        
        assert result['status'] == 'completed'
        assert len(result['top_features']) == 2
        
    finally:
        # Cleanup
        if expected_path.exists():
            expected_path.unlink()
        if Path(temp_path).exists():
            Path(temp_path).unlink()
