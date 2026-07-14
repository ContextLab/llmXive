"""
Integration tests for correlations.py
"""
import numpy as np
import pandas as pd
from code.analysis.correlations import run_correlations_with_fd_covariate, apply_fdr_correction

def test_correlation_with_synthetic_data():
    """
    Test correlation analysis with synthetic data that has known correlations.
    """
    # Generate synthetic data
    n_subjects = 50
    np.random.seed(42)
    
    # Create a metric that is correlated with motor_score
    motor_score = np.random.normal(0, 1, n_subjects)
    # Correlation r=0.5
    metric = 0.5 * motor_score + np.random.normal(0, 0.866, n_subjects)
    fd = np.random.normal(0, 1, n_subjects)
    
    df = pd.DataFrame({
        "subject_id": [f"sub-{i}" for i in range(n_subjects)],
        "modularity": metric,
        "global_efficiency": np.random.normal(0, 1, n_subjects),
        "participation_coef": np.random.normal(0, 1, n_subjects),
        "within_module_degree": np.random.normal(0, 1, n_subjects),
        "motor_score": motor_score,
        "fd": fd
    })
    
    # Run correlations
    results = run_correlations_with_fd_covariate(df, "motor_score")
    
    # Check that modularity has a significant correlation (r ~ 0.5)
    mod_result = results[results["metric_name"] == "modularity"].iloc[0]
    
    # Check r value (allow some tolerance for noise)
    assert 0.3 < mod_result["r"] < 0.7, f"Correlation r={mod_result['r']} not close to 0.5"
    
    # Check p-value (should be significant)
    assert mod_result["p"] < 0.05, f"P-value {mod_result['p']} not significant"
    
    print("Test passed: Correlation with synthetic data works.")
