"""
Contract test for the permutation test logic in compare_distributions.py.

This test defines the expected interface and behavior of the permutation test
implementation. It should be written first to define the interface.
"""
import pytest
import json
from pathlib import Path
import sys
import os

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root / "code"))

from utils.config import get_project_root

def test_permutation_test_interface_exists():
    """Test that the permutation test function exists and has the correct signature."""
    from code_03_statistical_analysis_compare_distributions import blocked_permutation_test
    
    # Check function exists
    assert callable(blocked_permutation_test)
    
    # Check it accepts the expected arguments
    human_counts = [1, 2, 3, 4, 5]
    llm_counts = [2, 3, 4, 5, 6]
    
    result = blocked_permutation_test(human_counts, llm_counts, n_permutations=100, seed=42)
    
    # Check result structure
    assert 'observed_diff' in result
    assert 'p_value' in result
    assert 'effect_size' in result
    assert 'n_permutations' in result
    
    # Check types
    assert isinstance(result['observed_diff'], float)
    assert isinstance(result['p_value'], float)
    assert isinstance(result['effect_size'], float)
    assert isinstance(result['n_permutations'], int)
    
    # Check p-value is between 0 and 1
    assert 0.0 <= result['p_value'] <= 1.0

def test_bonferroni_correction():
    """Test that Bonferroni correction is applied correctly."""
    from code_03_statistical_analysis_compare_distributions import apply_bonferroni_correction
    
    p_values = [0.01, 0.02, 0.03, 0.04]
    corrected = apply_bonferroni_correction(p_values)
    
    assert len(corrected) == len(p_values)
    assert all(0.0 <= p <= 1.0 for p in corrected)
    assert corrected[0] == min(0.01 * 4, 1.0)  # 4 smells
    assert corrected[1] == min(0.02 * 4, 1.0)

def test_confidence_interval():
    """Test that confidence interval is calculated correctly."""
    from code_03_statistical_analysis_compare_distributions import calculate_confidence_interval
    
    human_counts = [1, 2, 3, 4, 5]
    llm_counts = [2, 3, 4, 5, 6]
    
    ci = calculate_confidence_interval(human_counts, llm_counts)
    
    assert isinstance(ci, tuple)
    assert len(ci) == 2
    assert ci[0] <= ci[1]

def test_run_comparison():
    """Test that the run_comparison function returns the expected structure."""
    # This test assumes the data file exists
    # We'll skip if the file doesn't exist
    metrics_path = get_project_root() / "data" / "processed" / "smell_metrics.csv"
    if not metrics_path.exists():
        pytest.skip("Processed metrics file not found. Skipping test.")
    
    from code_03_statistical_analysis_compare_distributions import run_comparison
    
    results = run_comparison()
    
    assert isinstance(results, dict)
    assert 'Long Method' in results
    assert 'Duplicated Code' in results
    assert 'Feature Envy' in results
    assert 'Long Parameter List' in results
    
    for smell_type, result in results.items():
        assert 'observed_diff' in result
        assert 'p_value' in result
        assert 'corrected_p_value' in result
        assert 'effect_size' in result
        assert 'confidence_interval' in result
        assert 'n_human' in result
        assert 'n_llm' in result

if __name__ == "__main__":
    pytest.main([__file__, "-v"])