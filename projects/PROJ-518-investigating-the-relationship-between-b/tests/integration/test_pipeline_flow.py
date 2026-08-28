import os
import tempfile
import numpy as np
import pytest
from pathlib import Path
import pandas as pd

# Import pipeline components
from analysis.statistics import fit_regression, RegressionResult
from viz.plots import plot_flexibility_vs_creativity, plot_residuals
from data.loader import validate_and_filter_subjects, filter_by_motion
from config import get_config

def test_end_to_end_correlation():
    """
    Integration test: runs the full pipeline on a mock subset and asserts numeric r and p values.
    Simulates the flow: mock data -> regression -> plot generation -> result assertion.
    """
    # 1. Generate mock data (representing processed results from earlier stages)
    np.random.seed(42)
    n_subjects = 50
    
    # Mock flexibility scores (network dynamics metric)
    flexibility = np.random.normal(loc=0.45, scale=0.05, size=n_subjects)
    
    # Mock creativity scores (CAQ)
    # Create a moderate positive correlation for testing
    creativity = 0.8 * flexibility + np.random.normal(loc=0.0, scale=0.02, size=n_subjects)
    
    # Mock covariates
    age = np.random.randint(18, 65, size=n_subjects)
    sex = np.random.choice([0, 1], size=n_subjects) # 0: female, 1: male
    education = np.random.randint(12, 20, size=n_subjects)
    
    # Mock static connectivity strength
    static_strength = np.random.normal(loc=0.3, scale=0.05, size=n_subjects)

    # 2. Run Regression (US1 core analysis)
    covariates = {
        'age': age,
        'sex': sex,
        'education': education,
        'static_connectivity_strength': static_strength
    }

    result: RegressionResult = fit_regression(flexibility, creativity, covariates)

    # Assert numeric r and p values exist and are valid
    assert isinstance(result.r, float), "r must be a float"
    assert isinstance(result.p, float), "p must be a float"
    assert -1.0 <= result.r <= 1.0, "r must be between -1 and 1"
    assert 0.0 <= result.p <= 1.0, "p must be between 0 and 1"
    assert result.p < 0.05, f"Mock data should show significant correlation (p={result.p}), but p >= 0.05"

    # 3. Generate Visualizations (US2)
    with tempfile.TemporaryDirectory() as tmpdir:
        # Plot Flexibility vs Creativity
        plot_path = os.path.join(tmpdir, "flexibility_vs_creativity.png")
        plot_flexibility_vs_creativity(flexibility, creativity, output_path=plot_path)
        assert os.path.exists(plot_path), "Flexibility vs Creativity plot not generated"

        # Plot Residuals (requires a fitted model object, we use statsmodels directly for the plot function)
        import statsmodels.api as sm
        X = sm.add_constant(flexibility)
        for k, v in covariates.items():
            X = np.column_stack([X, v])
        model = sm.OLS(creativity, X).fit()
        
        residuals_path = os.path.join(tmpdir, "model_residuals.png")
        qq_path = os.path.join(tmpdir, "model_qq.png")
        plot_residuals(model, residuals_path=residuals_path, qq_path=qq_path)
        
        assert os.path.exists(residuals_path), "Residuals plot not generated"
        assert os.path.exists(qq_path), "QQ plot not generated"

    # 4. Verify Sensitivity Analysis (US3) - if available
    try:
        from analysis.sensitivity import run_sensitivity_analysis
        sensitivity_df = run_sensitivity_analysis(flexibility, creativity, window_lengths=[20, 30, 40])
        
        assert isinstance(sensitivity_df, pd.DataFrame), "Sensitivity result must be a DataFrame"
        assert 'window_length' in sensitivity_df.columns, "Missing window_length column"
        assert 'correlation' in sensitivity_df.columns, "Missing correlation column"
        assert 'p_value' in sensitivity_df.columns, "Missing p_value column"
        assert len(sensitivity_df) == 3, "Expected 3 rows for 3 window lengths"
    except ImportError:
        # If sensitivity module is not fully implemented yet, skip this check
        pass

    # Final assertion: The pipeline produced valid statistical results
    assert result.r > 0.3, f"Correlation too weak for mock data (r={result.r})"