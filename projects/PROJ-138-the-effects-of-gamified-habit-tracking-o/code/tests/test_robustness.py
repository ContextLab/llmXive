"""
Tests for robustness validation module.
"""
import os
import sys
import tempfile
import shutil
import pytest
import pandas as pd
import numpy as np
from code.analysis.robustness import bootstrap_effect_size

def generate_test_bootstrap_data():
    """
    Generate a small synthetic dataset for testing bootstrapping.
    This is used ONLY for unit testing the statistical logic,
    not for the final research data.
    """
    np.random.seed(42)
    n_users = 50
    n_weeks = 10
    
    data = []
    for user_id in range(n_users):
        # Random gamification status
        gam_status = np.random.choice([True, False])
        # Random conscientiousness
        consc = np.random.normal(50, 10)
        
        for week in range(1, n_weeks + 1):
            # Generate adherence based on status and week
            base_prob = 0.6 if gam_status else 0.4
            adherence = np.random.binomial(1, base_prob)
            
            data.append({
                "user_id": f"user_{user_id}",
                "gamification_status": gam_status,
                "conscientiousness_score": consc,
                "week_number": week,
                "weekly_adherence_flag": adherence
            })
    
    return pd.DataFrame(data)

def test_bootstrap_variance():
    """
    Test that bootstrapping generates samples and reports a coefficient variance.
    Verifies FR-004 and SC-004.
    """
    df = generate_test_bootstrap_data()
    
    # Run with a small number of iterations for speed in testing
    results = bootstrap_effect_size(df, n_iterations=10)
    
    # Assertions
    assert isinstance(results, dict)
    assert "variance" in results
    assert "ci_lower" in results
    assert "ci_upper" in results
    assert "n_valid" in results
    
    # Variance should be a non-negative float
    assert isinstance(results["variance"], float)
    assert results["variance"] >= 0
    
    # CI bounds should be numbers
    assert isinstance(results["ci_lower"], float)
    assert isinstance(results["ci_upper"], float)
    
    # Should have at least some valid iterations
    assert results["n_valid"] > 0