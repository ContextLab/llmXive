import os
import json
import pandas as pd
import numpy as np
import pytest
from pathlib import Path

# Mock the project structure for testing if run standalone
# In the actual project, these imports work because they are in the same directory
try:
    from code.config import get_results_path
    from code.utils import causal_language_scanner
except ImportError:
    # Fallback for running tests from root if path not set up
    pass

# Import the functions from the module under test
# We assume the module is importable as 'code.03_model' or similar
# Since the file is '03_model.py' in 'code/', we need to handle the import carefully
# In a real test environment, sys.path would include the project root or code/
import importlib.util
spec = importlib.util.spec_from_file_location("model_03", "code/03_model.py")
model_03 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model_03)

from model_03 import (
    run_sensitivity_analysis, 
    verify_robustness, 
    benjamini_hochberg
)

@pytest.fixture
def sample_data():
    """Create a synthetic dataset for testing sensitivity analysis logic."""
    np.random.seed(42)
    n = 100
    df = pd.DataFrame({
        'participant_id': range(n),
        'cognitive_flexibility_score': np.random.randn(n) * 10 + 50,
        'switching_index': np.random.randn(n) * 5 + 10,
        'num_platforms': np.random.randint(2, 10, n),
        'switching_frequency': np.random.randn(n) * 2 + 5,
        'total_screen_time': np.random.randn(n) * 20 + 100,
        'age': np.random.randint(18, 80, n)
    })
    # Ensure no NaNs for simplicity in this test
    return df

def test_benjamini_hochberg():
    """Test BH correction with known values."""
    p_values = [0.01, 0.04, 0.03, 0.005, 0.06]
    # Expected adjusted p-values for BH (sorted: 0.005, 0.01, 0.03, 0.04, 0.06)
    # n=5
    # 0.005 * 5/1 = 0.025
    # 0.01 * 5/2 = 0.025
    # 0.03 * 5/3 = 0.05
    # 0.04 * 5/4 = 0.05
    # 0.06 * 5/5 = 0.06
    # Monotonicity check (backwards):
    # 0.06
    # 0.05 (min(0.05, 0.06))
    # 0.05 (min(0.05, 0.05))
    # 0.025 (min(0.025, 0.05))
    # 0.025 (min(0.025, 0.025))
    # Mapping back to original order:
    # 0.01 -> 0.025
    # 0.04 -> 0.05
    # 0.03 -> 0.05
    # 0.005 -> 0.025
    # 0.06 -> 0.06
    
    results = model_03.benjamini_hochberg(p_values)
    # results is list of (idx, adj_p, is_sig)
    adj_p_values = [r[1] for r in sorted(results, key=lambda x: x[0])]
    
    expected = [0.025, 0.05, 0.05, 0.025, 0.06]
    
    for i, (calc, exp) in enumerate(zip(adj_p_values, expected)):
        assert abs(calc - exp) < 1e-6, f"Mismatch at index {i}: {calc} != {exp}"

def test_run_sensitivity_analysis(sample_data):
    """Test that sensitivity analysis runs and returns expected columns."""
    # Ensure required columns exist
    required = ['cognitive_flexibility_score', 'switching_index', 'num_platforms', 
                'switching_frequency', 'total_screen_time', 'age']
    for col in required:
        assert col in sample_data.columns
    
    result_df = run_sensitivity_analysis(sample_data)
    
    assert not result_df.empty
    assert 'definition' in result_df.columns
    assert 'beta' in result_df.columns
    assert 'p_value' in result_df.columns
    assert 'n' in result_df.columns
    assert 'sign' in result_df.columns
    assert 'delta_beta' in result_df.columns
    assert 'fdr_p_value' in result_df.columns
    
    # Check that all three definitions are present
    definitions = set(result_df['definition'].unique())
    expected_defs = {'main', 'platform_count_only', 'frequency_only'}
    assert definitions == expected_defs

def test_verify_robustness_sign_flip():
    """Test robustness verification when signs flip."""
    df = pd.DataFrame({
        'definition': ['main', 'sensitivity1', 'sensitivity2'],
        'beta': [0.5, -0.2, 0.3], # Sign flip
        'p_value': [0.01, 0.02, 0.03],
        'fdr_p_value': [0.02, 0.04, 0.06],
        'sign': [1, -1, 1]
    })
    
    evidence = verify_robustness(df)
    assert evidence['sc003_status'] == 'FAIL'
    assert 'Sign instability' in evidence['message']

def test_verify_robustness_high_p():
    """Test robustness verification when p > 0.10."""
    df = pd.DataFrame({
        'definition': ['main', 'sensitivity1', 'sensitivity2'],
        'beta': [0.5, 0.4, 0.6], # Stable sign
        'p_value': [0.01, 0.15, 0.03], # One high p
        'fdr_p_value': [0.02, 0.20, 0.06], # FDR also high
        'sign': [1, 1, 1]
    })
    
    evidence = verify_robustness(df)
    assert evidence['sc003_status'] == 'FAIL'
    assert 'p > 0.10' in evidence['message']

def test_verify_robustness_pass():
    """Test robustness verification when all conditions met."""
    df = pd.DataFrame({
        'definition': ['main', 'sensitivity1', 'sensitivity2'],
        'beta': [0.5, 0.4, 0.6],
        'p_value': [0.01, 0.02, 0.03],
        'fdr_p_value': [0.02, 0.04, 0.06],
        'sign': [1, 1, 1]
    })
    
    evidence = verify_robustness(df)
    assert evidence['sc003_status'] == 'PASS'
    assert 'Met' in evidence['message']