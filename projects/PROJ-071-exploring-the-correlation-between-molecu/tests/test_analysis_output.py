import json
import pytest
from pathlib import Path
import sys
import os

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from config import get_config

@pytest.fixture
def config():
    return get_config()

def test_analysis_results_json_exists_and_valid(config):
    """
    T026 Test: Verify analysis_results.json exists, contains R2 key, and passes JSON schema validation.
    """
    output_path = Path(config['paths']['processed']) / 'analysis_results.json'
    
    # 1. File exists
    assert output_path.exists(), f"File {output_path} does not exist. T026 failed."
    
    # 2. Load and validate JSON
    try:
        with open(output_path, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        pytest.fail(f"File {output_path} is not valid JSON: {e}")
    
    # 3. Verify R2 key exists in MLR and Lasso sections
    assert 'mlr' in data, "Missing 'mlr' key in analysis_results.json"
    assert 'r_squared' in data['mlr'], "Missing 'r_squared' in 'mlr' results"
    
    assert 'lasso' in data, "Missing 'lasso' key in analysis_results.json"
    assert 'cv_r2_mean' in data['lasso'], "Missing 'cv_r2_mean' in 'lasso' results"
    
    # 4. Verify other expected keys
    assert 'sensitivity_analysis' in data, "Missing 'sensitivity_analysis' key"
    assert 'residual_diagnostics' in data, "Missing 'residual_diagnostics' key"
    assert 'correlation_significance_pass' in data, "Missing 'correlation_significance_pass' key"
    assert 'residual_diagnostics_pass' in data, "Missing 'residual_diagnostics_pass' key"
    
    # 5. Check types
    assert isinstance(data['mlr']['r_squared'], (int, float)), "R2 should be a number"
    assert isinstance(data['correlation_significance_pass'], bool), "Pass flags should be booleans"

def test_sensitivity_analysis_json_exists(config):
    """
    Verify T022a output: sensitivity_analysis.json exists.
    """
    output_path = Path(config['paths']['processed']) / 'sensitivity_analysis.json'
    assert output_path.exists(), f"File {output_path} does not exist. T022a failed."
    
    with open(output_path, 'r') as f:
        data = json.load(f)
    
    assert isinstance(data, list), "Sensitivity analysis should be a list"
    if len(data) > 0:
        assert 'threshold' in data[0], "Missing 'threshold' in sensitivity entry"
        assert 'significant_count' in data[0], "Missing 'significant_count' in sensitivity entry"