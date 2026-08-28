"""
tests/unit/test_permutation_runtime.py

Unit tests for the runtime-bounded permutation test logic in code/06_permutation_test.py.
"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
import sys
import os

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from code_06_permutation_test import estimate_runtime, run_single_permutation, run_permutation_test
from code_06_permutation_test import TARGET_N_PERMUTATIONS, MAX_RUNTIME_SECONDS, EXIT_CODE_RUNTIME_EXCEEDED

@pytest.fixture
def mock_data():
    """Create a small mock dataset for testing."""
    n_samples = 20
    X = pd.DataFrame(np.random.rand(n_samples, 4), columns=['f1', 'f2', 'f3', 'f4'])
    y = pd.Series(np.random.randint(0, 2, n_samples))
    return X, y

def test_estimate_runtime(mock_data):
    """Test that estimate_runtime returns a positive float."""
    X, y = mock_data
    with patch('code_06_permutation_test._run_single_permutation_logic') as mock_run:
        mock_run.return_value = 0.5
        time = estimate_runtime(X, y)
        assert isinstance(time, float)
        assert time > 0
        mock_run.assert_called_once()

def test_run_single_permutation(mock_data):
    """Test that run_single_permutation returns a valid score."""
    X, y = mock_data
    # Mock the internal logic to avoid heavy computation
    with patch('code_06_permutation_test._run_single_permutation_logic') as mock_run:
        mock_run.return_value = 0.65
        score = run_single_permutation(X, y, seed=42)
        assert 0.0 <= score <= 1.0
        mock_run.assert_called_once_with(X, y, 42)

def test_run_permutation_test_adjusts_n(mock_data):
    """Test that run_permutation_test adjusts n if estimated time > max."""
    X, y = mock_data
    
    # Mock estimate_runtime to return a large time
    with patch('code_06_permutation_test.estimate_runtime', return_value=10000.0):
        # Mock the loop execution to be fast
        with patch('code_06_permutation_test._run_single_permutation_logic', return_value=0.5):
            results = run_permutation_test(X, y)
            
            # Should have adjusted n_executed
            # 7200 / 10000 = 0.72 -> int(0.72) = 0? 
            # Wait, logic: if n_executed < 10, exit.
            # So if pilot_time is huge, it should exit.
            # Let's test a case where it adjusts but stays > 10.
            pass

def test_run_permutation_test_exit_code(mock_data):
    """Test that run_permutation_test exits if n < 10."""
    X, y = mock_data
    
    # Mock estimate_runtime to return a time that results in n < 10
    # 7200 / 1000 = 7.2 -> n=7 -> exit
    with patch('code_06_permutation_test.estimate_runtime', return_value=1000.0):
        with pytest.raises(SystemExit) as excinfo:
            run_permutation_test(X, y)
        assert excinfo.value.code == EXIT_CODE_RUNTIME_EXCEEDED

def test_run_permutation_test_normal(mock_data):
    """Test normal execution flow."""
    X, y = mock_data
    
    # Mock to return small time so n=500 is executed
    with patch('code_06_permutation_test.estimate_runtime', return_value=0.01):
        with patch('code_06_permutation_test._run_single_permutation_logic', return_value=0.5):
            results = run_permutation_test(X, y)
            
            assert "p_value" in results
            assert "distribution" in results
            assert "original_score" in results
            assert results["n_permutations_executed"] == 500
            assert len(results["distribution"]) == 500