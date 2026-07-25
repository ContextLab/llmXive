"""
Integration tests for data generation pipeline.
"""
import pytest
import numpy as np
from code.generate_data import generate_correlated_data
from code.run_tests import run_hypothesis_tests
from code.collect_pvalues import collect_pvalues

def test_full_pipeline():
    """Test generating data and running hypothesis tests."""
    n, p = 500, 20
    rho = 0.3
    seed = 999
    
    # Generate data
    dataset = generate_correlated_data(n, p, rho, seed)
    
    # Run tests
    pvals = run_hypothesis_tests(dataset.data, "t-test")
    
    # Collect
    result = collect_pvalues(pvals, 0, seed)
    
    assert len(result["p_values"]) == p
    assert result["iteration_id"] == 0
