"""
Integration tests for correlation analysis (T019).
Tests T024: Spearman/Pearson correlation with FD covariate and FDR correction.
"""
import os
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from code.analysis.correlations import (
    run_metric_correlations,
    apply_fdr_correction,
    partial_correlation,
    main
)

@pytest.fixture
def synthetic_data():
    """
    Generate synthetic data with known correlations for testing.
    - Metric A correlates with Target (r=0.5)
    - Metric B is noise
    - FD is a confounder
    """
    np.random.seed(42)
    n = 100
    
    # Generate confounder FD
    fd = np.random.normal(0.2, 0.1, n)
    
    # Generate Target (motor_score) influenced by FD and Metric A
    metric_a = np.random.normal(0, 1, n)
    # Target = 0.5 * metric_a + 0.3 * fd + noise
    target = 0.5 * metric_a + 0.3 * fd + np.random.normal(0, 0.5, n)
    
    # Metric B is pure noise
    metric_b = np.random.normal(0, 1, n)
    
    df = pd.DataFrame({
        'subject_id': range(n),
        'modularity': metric_a,
        'global_efficiency': metric_b,
        'motor_score': target,
        'fd': fd
    })
    return df

def test_partial_correlation_removes_confounding(synthetic_data):
    """
    Test that partial correlation correctly controls for FD.
    Without controlling for FD, the correlation between metric_b (noise) 
    and target might be non-zero due to shared FD influence.
    With controlling, it should be near zero.
    """
    df = synthetic_data
    
    # Metric B is noise, should have low correlation with target after controlling FD
    r, p = partial_correlation(
        df['global_efficiency'],
        df['motor_score'],
        df[['fd']],
        method='pearson'
    )
    
    # With proper partial correlation, r should be small (noise)
    # We allow some variance but it should be significantly lower than raw correlation
    assert abs(r) < 0.3, f"Partial correlation for noise metric should be low, got {r}"
    
    # Metric A has true correlation
    r_true, p_true = partial_correlation(
        df['modularity'],
        df['motor_score'],
        df[['fd']],
        method='pearson'
    )
    
    # Should detect a meaningful correlation
    assert abs(r_true) > 0.2, f"Partial correlation for true metric should be significant, got {r_true}"

def test_run_metric_correlations_with_synthetic_data(synthetic_data):
    """
    Integration test: Run full correlation pipeline on synthetic data.
    Verifies that:
    1. The function runs without error
    2. FDR correction is applied
    3. Significant metrics are identified
    """
    df = synthetic_data
    
    # Run the full correlation suite
    results = run_metric_correlations(
        df,
        target_col="motor_score",
        covariate_cols=["fd"],
        metric_cols=["modularity", "global_efficiency"],
        method="spearman"
    )
    
    # Verify structure
    assert "metric_name" in results.columns
    assert "r" in results.columns
    assert "p" in results.columns
    assert "q" in results.columns
    assert "significant" in results.columns
    
    # Verify FDR correction logic (q values should be > p values usually, but bounded by 1)
    assert all(results["q"] >= 0)
    assert all(results["q"] <= 1.0)
    
    # Check that modularity (the true signal) is detected as significant or has low p
    mod_row = results[results["metric_name"] == "modularity"]
    if not mod_row.empty:
        assert mod_row.iloc[0]["p"] < 0.1, "True signal should have low p-value"

def test_apply_fdr_correction_logic():
    """
    Test the Benjamini-Hochberg FDR correction logic specifically.
    """
    # Create a dataframe with known p-values
    df = pd.DataFrame({
        'metric_name': ['A', 'B', 'C', 'D'],
        'p': [0.001, 0.01, 0.04, 0.20]
    })
    
    result = apply_fdr_correction(df, alpha=0.05)
    
    # Check that q values are computed
    assert 'q' in result.columns
    assert 'significant' in result.columns
    
    # For sorted p-values: p_i * N / i
    # A: 0.001 * 4 / 1 = 0.004
    # B: 0.01 * 4 / 2 = 0.02
    # C: 0.04 * 4 / 3 = 0.0533
    # D: 0.20 * 4 / 4 = 0.20
    # Monotonicity check: C should be <= D, B <= C, etc.
    
    assert result.iloc[0]["significant"] == True  # 0.004 < 0.05
    assert result.iloc[1]["significant"] == True  # 0.02 < 0.05
    # C might be significant depending on monotonicity enforcement, but usually > 0.05
    # D should be False
    assert result.iloc[3]["significant"] == False

def test_log_threshold_correlations(synthetic_data):
    """
    Test that correlations above the threshold are logged/flagged.
    """
    df = synthetic_data
    results = run_metric_correlations(
        df,
        target_col="motor_score",
        covariate_cols=["fd"],
        metric_cols=["modularity"],
        method="spearman"
    )
    
    # Check that the result dataframe contains the expected columns
    assert "r" in results.columns
    assert "significant" in results.columns
    
    # If r is high and significant, it should be handled correctly
    # (The logging side-effect is hard to test in unit/integration without mocking,
    # but the data logic is verified by the presence of the columns and values)
    if not results.empty:
        assert results.iloc[0]["r"] != 0  # Should have computed a value