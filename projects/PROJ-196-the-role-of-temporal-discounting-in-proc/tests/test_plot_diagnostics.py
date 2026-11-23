"""
Unit tests for the model diagnostics visualization module.
"""
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import pandas as pd
import numpy as np
import statsmodels.api as sm
from scipy import stats as scipy_stats

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from visualizations.plot_diagnostics import (
    plot_residuals_vs_fitted,
    plot_q_q_plot,
    plot_scale_location,
    generate_diagnostics_report,
    run_ols_regression,
    ensure_directories
)

@pytest.fixture
def mock_ols_results():
    """Create a mock OLS results object for testing."""
    # Create dummy data
    n = 100
    X = np.random.randn(n, 2)
    X = sm.add_constant(X)
    y = np.random.randn(n)
    
    model = sm.OLS(y, X)
    results = model.fit()
    return results

@pytest.fixture
def temp_dir():
    """Create a temporary directory for output files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_ensure_directories(temp_dir):
    """Test that ensure_directories creates the directory."""
    test_dir = temp_dir / "test_diagnostics"
    with patch('visualizations.plot_diagnostics.DIAGNOSTICS_DIR', test_dir):
        ensure_directories()
        assert test_dir.exists()
        assert test_dir.is_dir()

def test_plot_residuals_vs_fitted(mock_ols_results, temp_dir):
    """Test residuals vs fitted plot generation."""
    save_path = temp_dir / "residuals.png"
    
    inspection = plot_residuals_vs_fitted(mock_ols_results, save_path)
    
    assert save_path.exists()
    assert "plot_type" in inspection
    assert inspection["plot_type"] == "residuals_vs_fitted"
    assert "correlation_fitted_residuals" in inspection
    assert "p_value" in inspection
    assert "interpretation" in inspection
    assert isinstance(inspection["correlation_fitted_residuals"], float)
    assert isinstance(inspection["p_value"], float)

def test_plot_q_q_plot(mock_ols_results, temp_dir):
    """Test Q-Q plot generation."""
    save_path = temp_dir / "qq_plot.png"
    
    inspection = plot_q_q_plot(mock_ols_results, save_path)
    
    assert save_path.exists()
    assert "plot_type" in inspection
    assert inspection["plot_type"] == "qq_plot"
    assert "shapiro_statistic" in inspection
    assert "shapiro_p_value" in inspection
    assert "interpretation" in inspection
    assert isinstance(inspection["shapiro_statistic"], float)
    assert isinstance(inspection["shapiro_p_value"], float)

def test_plot_scale_location(mock_ols_results, temp_dir):
    """Test Scale-Location plot generation."""
    save_path = temp_dir / "scale_location.png"
    
    inspection = plot_scale_location(mock_ols_results, save_path)
    
    assert save_path.exists()
    assert "plot_type" in inspection
    assert inspection["plot_type"] == "scale_location"
    assert "correlation_fitted_sqrt_resid" in inspection
    assert "p_value" in inspection
    assert "interpretation" in inspection
    assert isinstance(inspection["correlation_fitted_sqrt_resid"], float)
    assert isinstance(inspection["p_value"], float)

def test_generate_diagnostics_report():
    """Test the report generation function."""
    inspections = [
        {
            "plot_type": "residuals_vs_fitted",
            "correlation_fitted_residuals": 0.01,
            "p_value": 0.8,
            "interpretation": "No pattern"
        },
        {
            "plot_type": "qq_plot",
            "shapiro_statistic": 0.95,
            "shapiro_p_value": 0.4,
            "interpretation": "Normal"
        },
        {
            "plot_type": "scale_location",
            "correlation_fitted_sqrt_resid": 0.02,
            "p_value": 0.7,
            "interpretation": "Homoscedasticity"
        }
    ]
    
    report = generate_diagnostics_report(inspections)
    
    assert "model_assumptions_check" in report
    assert "summary" in report
    assert report["summary"]["all_assumptions_met"] is True
    assert len(report["summary"]["plots_generated"]) == 3

def test_generate_diagnostics_report_failure_case():
    """Test report generation when assumptions are not met."""
    inspections = [
        {
            "plot_type": "residuals_vs_fitted",
            "correlation_fitted_residuals": 0.5,
            "p_value": 0.01,
            "interpretation": "Pattern detected"
        },
        {
            "plot_type": "qq_plot",
            "shapiro_statistic": 0.8,
            "shapiro_p_value": 0.001,
            "interpretation": "Non-normal residuals"
        },
        {
            "plot_type": "scale_location",
            "correlation_fitted_sqrt_resid": 0.4,
            "p_value": 0.02,
            "interpretation": "Heteroscedasticity detected"
        }
    ]
    
    report = generate_diagnostics_report(inspections)
    
    assert report["summary"]["all_assumptions_met"] is False

def test_run_ols_regression():
    """Test OLS regression function with sample data."""
    # Create sample data
    n = 50
    df = pd.DataFrame({
        'procrastination': np.random.randn(n),
        'log_k': np.random.randn(n),
        'wm_metric': np.random.randn(n),
        'age': np.random.randint(18, 65, n),
        'gender': np.random.choice(['male', 'female'], n)
    })
    
    # Add interaction term
    df['log_k:wm_metric'] = df['log_k'] * df['wm_metric']
    
    results = run_ols_regression(df)
    
    assert results is not None
    assert hasattr(results, 'fittedvalues')
    assert hasattr(results, 'resid')
    assert len(results.fittedvalues) == n