import pytest
import pandas as pd
import numpy as np
import os
import tempfile
from regression_analysis import run_ols_regression, detect_percolation_threshold, analyze_scaling_law

def test_regression_outputs():
    """Verify exponent, CI, and p-value calculation."""
    # Create temp CSV
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        f.write("seed,N,p,avg_degree,conductivity,percolation_flag,scaling_factor\n")
        # Generate some connected data
        for i, deg in enumerate([2, 3, 4, 5, 6, 7, 8]):
            # conductivity roughly scales with degree
            k = deg * 10 + np.random.rand() * 2
            f.write(f"{i},{100},0.1,{deg},{k:.2f},1,1.0\n")
        temp_path = f.name
    
    try:
        results = run_ols_regression(temp_path)
        assert results is not None
        assert 'exponent' in results
        assert 'p_value' in results
        assert 'ci_lower' in results
        assert 'ci_upper' in results
        assert results['p_value'] > 0  # p-value should be valid
    finally:
        os.unlink(temp_path)

def test_percolation_threshold_logic():
    """Verify 80% connectivity cutoff logic."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        f.write("seed,N,p,avg_degree,conductivity,percolation_flag,scaling_factor\n")
        # Create data where degree 4 has 100% connected, degree 3 has 50%
        # Degree 2 has 0%
        f.write("1,100,0.1,2,0,0,1.0\n")
        f.write("2,100,0.1,2,0,0,1.0\n")
        f.write("3,100,0.1,3,10,0,1.0\n") # 50% connected (1 out of 2? No, let's do 1/2=0.5)
        f.write("4,100,0.1,3,10,1,1.0\n")
        f.write("5,100,0.1,4,20,1,1.0\n")
        f.write("6,100,0.1,4,20,1,1.0\n")
        f.write("7,100,0.1,4,20,1,1.0\n") # 3/3 = 100%
        temp_path = f.name
    
    try:
        # Degree 3: 1/2 = 0.5 (50%)
        # Degree 4: 3/3 = 1.0 (100%)
        # Threshold should be 4 (first >= 80%)
        threshold = detect_percolation_threshold(temp_path)
        assert threshold == 4.0
    finally:
        os.unlink(temp_path)