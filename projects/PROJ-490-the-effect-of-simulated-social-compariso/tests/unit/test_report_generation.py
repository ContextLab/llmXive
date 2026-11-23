import json
import os
import pytest
from pathlib import Path
import tempfile
import pandas as pd
import numpy as np

# Import the module under test
from analysis.report_generator import (
    generate_final_report,
    save_report,
    load_model_results,
    load_bootstrap_results,
    load_sensitivity_results,
    load_data_path
)
from data.config import get_config, reset_config


@pytest.fixture
def mock_processed_files(tmp_path):
    """
    Create mock files in data/processed for testing.
    """
    # Setup config to use tmp_path
    config = get_config()
    config["paths"]["processed"] = str(tmp_path)

    # Create mock regression coefficients CSV
    coeffs_df = pd.DataFrame({
        "term": ["Intercept", "avatar_condition", "pre_self_esteem", "comparison_tendency", "interaction"],
        "estimate": [2.5, 0.3, 0.8, -0.1, 0.2],
        "std_error": [0.1, 0.05, 0.08, 0.06, 0.09],
        "p_value": [0.001, 0.003, 0.0001, 0.15, 0.02],
        "ci_lower": [2.3, 0.2, 0.64, -0.22, 0.02],
        "ci_upper": [2.7, 0.4, 0.96, 0.02, 0.38]
    })
    coeffs_path = tmp_path / "regression_coefficients.csv"
    coeffs_df.to_csv(coeffs_path, index=False)

    # Create mock diagnostics JSON
    diagnostics = {
        "assumptions": {
            "normality": {"statistic": 0.98, "p_value": 0.45, "passed": True},
            "homoscedasticity": {"statistic": 1.2, "p_value": 0.30, "passed": True},
            "collinearity": {"max_vif": 2.1, "passed": True}
        },
        "collinearity_flags": [],
        "model_summary": {"r_squared": 0.65, "adj_r_squared": 0.63}
    }
    diag_path = tmp_path / "regression_diagnostics.json"
    with open(diag_path, "w") as f:
        json.dump(diagnostics, f)

    # Create mock bootstrap results JSON
    bootstrap = {
        "ci_width_variance": 0.005,
        "stability_flag": "PASS",
        "iterations": 1000,
        "coefficients": [
            {"term": "avatar_condition", "mean": 0.29, "ci_lower": 0.20, "ci_upper": 0.38},
            {"term": "interaction", "mean": 0.19, "ci_lower": 0.01, "ci_upper": 0.37}
        ]
    }
    boot_path = tmp_path / "bootstrap_results.json"
    with open(boot_path, "w") as f:
        json.dump(bootstrap, f)

    # Create mock sensitivity results JSON
    sensitivity = {
        "threshold_sensitivity": {
            "p_0.05": {"stable": True, "count": 1000},
            "p_0.01": {"stable": True, "count": 950}
        },
        "imputation_limits": {
            "low": {"stable": True},
            "moderate": {"stable": True},
            "high": {"stable": False}
        },
        "family_wise_error_correction": {
            "method": "holm",
            "adjusted_p_values": [0.002, 0.005, 0.0001, 0.25, 0.04]
        },
        "parameter_recovery": None,
        "overall_robustness": "PASS"
    }
    sens_path = tmp_path / "sensitivity_results.json"
    with open(sens_path, "w") as f:
        json.dump(sensitivity, f)

    # Create mock state file
    state_dir = tmp_path.parent / "state" / "projects"
    state_dir.mkdir(parents=True, exist_ok=True)
    state_path = state_dir / "PROJ-490-the-effect-of-simulated-social-compariso.yaml"
    
    import yaml
    state_data = {
        "artifact_hashes": {
            "data_source": {
                "path": "data/raw/synthetic_dataset.csv",
                "hash": "abc123"
            }
        }
    }
    with open(state_path, "w") as f:
        yaml.dump(state_data, f)

    return tmp_path


def test_load_model_results(mock_processed_files):
    """Test loading model results from mock files."""
    results = load_model_results()
    assert "coefficients" in results
    assert "diagnostics" in results
    assert len(results["coefficients"]) == 5
    assert results["diagnostics"]["assumptions"]["normality"]["passed"] is True


def test_load_bootstrap_results(mock_processed_files):
    """Test loading bootstrap results."""
    results = load_bootstrap_results()
    assert results["ci_width_variance"] == 0.005
    assert results["stability_flag"] == "PASS"
    assert results["iterations"] == 1000


def test_load_sensitivity_results(mock_processed_files):
    """Test loading sensitivity results."""
    results = load_sensitivity_results()
    assert "threshold_sensitivity" in results
    assert "overall_robustness" in results
    assert results["overall_robustness"] == "PASS"


def test_load_data_path(mock_processed_files):
    """Test loading data path from state file."""
    path = load_data_path()
    assert "synthetic_dataset.csv" in path


def test_generate_final_report(mock_processed_files):
    """Test generating the final report structure."""
    report = generate_final_report()

    # Check metadata
    assert "report_metadata" in report
    assert report["report_metadata"]["project_id"] == "PROJ-490-the-effect-of-simulated-social-compariso"
    assert report["report_metadata"]["task_id"] == "T030"
    assert "data_source_path" in report["report_metadata"]

    # Check model results
    assert "model_results" in report
    assert "coefficients" in report["model_results"]
    assert "assumptions_check" in report["model_results"]

    # Check bootstrap
    assert "bootstrap_stability" in report
    assert report["bootstrap_stability"]["stability_flag"] == "PASS"

    # Check sensitivity
    assert "sensitivity_findings" in report
    assert "threshold_sweep" in report["sensitivity_findings"]

    # Check conclusions
    assert "conclusions" in report
    assert report["conclusions"]["stability_assessment"] == "Stable"


def test_save_report(mock_processed_files):
    """Test saving the report to a JSON file."""
    report = generate_final_report()
    output_path = save_report(report)

    assert os.path.exists(output_path)
    with open(output_path, "r") as f:
        saved_report = json.load(f)
    
    assert saved_report["report_metadata"]["task_id"] == "T030"
    assert saved_report["model_results"]["coefficients"] == report["model_results"]["coefficients"]
