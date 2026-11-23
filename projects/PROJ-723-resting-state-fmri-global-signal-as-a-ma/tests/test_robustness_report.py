"""
Tests for T031: Robustness Report Generation.
Verifies that the report generation logic correctly aggregates results
from alpha sweep, variance analysis, and partial correlation.
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from robustness import generate_robustness_report
from utils import read_json

def test_generate_robustness_report_structure():
    """Test that the generated report has the expected structure."""
    # Mock data for alpha sweep
    alpha_sweep_data = {
        "alpha_values": [0.1, 1.0, 10.0],
        "metrics": [
            {"alpha": 0.1, "mae": 1.0, "r2": 0.5, "coefficients": [0.1]},
            {"alpha": 1.0, "mae": 1.1, "r2": 0.4, "coefficients": [0.05]},
            {"alpha": 10.0, "mae": 1.2, "r2": 0.3, "coefficients": [0.01]}
        ],
        "stability_summary": {
            "mae_range": [1.0, 1.2],
            "r2_range": [0.3, 0.5]
        }
    }

    # Mock data for variance analysis
    variance_data = {
        "metric": "Global_Signal_Variance",
        "pearson_r": 0.45,
        "p_value": 0.01,
        "sample_size": 100
    }

    # Mock data for partial correlation
    partial_corr_data = {
        "controlled_variable": "Mean_FD",
        "partial_correlation_r": 0.40,
        "p_value": 0.02,
        "degrees_of_freedom": 97,
        "significant_at_0_05": True
    }

    report = generate_robustness_report(
        alpha_sweep_data,
        variance_data,
        partial_corr_data,
        logger=MagicMock()
    )

    # Verify top-level keys
    assert "analysis_type" in report
    assert report["analysis_type"] == "robustness_sensitivity"
    assert "alpha_sweep" in report
    assert "variance_metric_analysis" in report
    assert "partial_correlation_analysis" in report
    assert "summary" in report

    # Verify summary keys
    assert "alpha_stable" in report["summary"]
    assert "variance_correlation_significant" in report["summary"]
    assert "partial_correlation_significant" in report["summary"]

    # Verify data integrity
    assert report["alpha_sweep"]["alpha_values"] == alpha_sweep_data["alpha_values"]
    assert report["variance_metric_analysis"]["pearson_r"] == variance_data["pearson_r"]
    assert report["partial_correlation_analysis"]["p_value"] == partial_corr_data["p_value"]

def test_generate_robustness_report_summary_logic():
    """Test that the summary logic correctly determines stability and significance."""
    # Case 1: Unstable alpha (large R2 swing), significant variance, significant partial
    alpha_sweep_unstable = {
        "alpha_values": [0.01, 1000.0],
        "metrics": [
            {"alpha": 0.01, "mae": 1.0, "r2": 0.8, "coefficients": []},
            {"alpha": 1000.0, "mae": 5.0, "r2": -0.1, "coefficients": []}
        ],
        "stability_summary": {"mae_range": [1.0, 5.0], "r2_range": [-0.1, 0.8]}
    }
    variance_sig = {"pearson_r": 0.5, "p_value": 0.01, "metric": "Var", "sample_size": 10}
    partial_sig = {"p_value": 0.01, "controlled_variable": "FD", "partial_correlation_r": 0.5, "degrees_of_freedom": 8, "significant_at_0_05": True}

    report = generate_robustness_report(alpha_sweep_unstable, variance_sig, partial_sig, logger=MagicMock())
    
    assert report["summary"]["alpha_stable"] is False
    assert report["summary"]["variance_correlation_significant"] is True
    assert report["summary"]["partial_correlation_significant"] is True

    # Case 2: Stable alpha, non-significant variance, non-significant partial
    alpha_sweep_stable = {
        "alpha_values": [1.0, 2.0],
        "metrics": [
            {"alpha": 1.0, "mae": 1.0, "r2": 0.5, "coefficients": []},
            {"alpha": 2.0, "mae": 1.01, "r2": 0.49, "coefficients": []}
        ],
        "stability_summary": {"mae_range": [1.0, 1.01], "r2_range": [0.49, 0.5]}
    }
    variance_non_sig = {"pearson_r": 0.1, "p_value": 0.5, "metric": "Var", "sample_size": 10}
    partial_non_sig = {"p_value": 0.6, "controlled_variable": "FD", "partial_correlation_r": 0.1, "degrees_of_freedom": 8, "significant_at_0_05": False}

    report2 = generate_robustness_report(alpha_sweep_stable, variance_non_sig, partial_non_sig, logger=MagicMock())

    assert report2["summary"]["alpha_stable"] is True
    assert report2["summary"]["variance_correlation_significant"] is False
    assert report2["summary"]["partial_correlation_significant"] is False