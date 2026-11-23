import numpy as np
import pytest
from analysis.sensitivity import run_sensitivity_analysis
from analysis.statistics import run_permutation_test

def test_run_sensitivity_analysis_structure():
    """Test that run_sensitivity_analysis returns the correct dictionary structure."""
    n_subjects = 50
    n_windows = 3
    window_lengths = [20, 30, 40]
    
    # Create mock data: 2D array (subjects, windows)
    np.random.seed(42)
    flexibility = np.random.rand(n_subjects, n_windows)
    creativity = np.random.rand(n_subjects)
    
    result = run_sensitivity_analysis(flexibility, creativity, window_lengths)
    
    assert isinstance(result, dict)
    assert 'p_values' in result
    assert 'correlations' in result
    assert 'window_lengths' in result
    
    assert isinstance(result['p_values'], list)
    assert isinstance(result['correlations'], list)
    assert isinstance(result['window_lengths'], list)
    
    assert len(result['p_values']) == n_windows
    assert len(result['correlations']) == n_windows
    assert len(result['window_lengths']) == n_windows
    
    assert result['window_lengths'] == window_lengths

def test_run_sensitivity_analysis_values():
    """Test that the returned values are floats and within expected ranges."""
    n_subjects = 50
    n_windows = 2
    window_lengths = [20, 30]
    
    np.random.seed(42)
    flexibility = np.random.rand(n_subjects, n_windows)
    creativity = np.random.rand(n_subjects)
    
    result = run_sensitivity_analysis(flexibility, creativity, window_lengths)
    
    for p in result['p_values']:
        assert 0.0 <= p <= 1.0
    
    for r in result['correlations']:
        assert -1.0 <= r <= 1.0

def test_run_sensitivity_analysis_length_mismatch():
    """Test that mismatched lengths raise an error."""
    flexibility = np.random.rand(50, 2)
    creativity = np.random.rand(50)
    window_lengths = [20, 30, 40] # 3 windows, but flexibility only has 2 columns
    
    with pytest.raises(ValueError, match="Number of flexibility vectors"):
        run_sensitivity_analysis(flexibility, creativity, window_lengths)

def test_run_sensitivity_analysis_list_input():
    """Test that the function accepts a list of arrays."""
    n_subjects = 50
    n_windows = 2
    window_lengths = [20, 30]
    
    np.random.seed(42)
    flex_list = [np.random.rand(n_subjects) for _ in range(n_windows)]
    creativity = np.random.rand(n_subjects)
    
    result = run_sensitivity_analysis(flex_list, creativity, window_lengths)
    
    assert len(result['p_values']) == n_windows
    assert len(result['correlations']) == n_windows
    assert result['window_lengths'] == window_lengths
