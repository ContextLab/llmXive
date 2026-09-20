"""
Integration Test for T029a: Model Metrics Generation

Tests that the model_metrics_generator script produces valid JSON with
required fields (adjusted R², RMSE, p-values, CV mean R²) and consumes
the sensitivity analysis artifact.
"""

import json
import os
import tempfile
from pathlib import Path
import pytest

from code.model_metrics_generator import (
    load_json_file,
    save_json_file,
    generate_model_metrics_report
)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test artifacts."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def mock_model_results(temp_dir):
    """Create a mock model_results.json file."""
    data = {
        "lmm": {
            "adjusted_r_squared": 0.75,
            "rmse": 1.23,
            "p_values": {
                "phosphorus": 0.001,
                "nitrogen": 0.025
            },
            "cv_mean_r_squared": 0.72
        },
        "random_forest": {
            "r_squared": 0.68,
            "rmse": 1.45,
            "cv_mean_r_squared": 0.65
        }
    }
    path = temp_dir / "model_results.json"
    save_json_file(path, data)
    return path

@pytest.fixture
def mock_sensitivity_analysis(temp_dir):
    """Create a mock sensitivity_analysis.json file."""
    data = {
        "literature_overlap": True,
        "observed_coefficient": 0.45,
        "percent_deviation": 5.2,
        "literature_mean": 0.48,
        "confidence_interval": [0.42, 0.50]
    }
    path = temp_dir / "sensitivity_analysis.json"
    save_json_file(path, data)
    return path

def test_generate_model_metrics_report_success(
    temp_dir, mock_model_results, mock_sensitivity_analysis
):
    """Test successful generation of model metrics report."""
    output_path = temp_dir / "model_metrics_raw.json"

    report = generate_model_metrics_report(
        mock_model_results,
        mock_sensitivity_analysis,
        output_path
    )

    # Verify file was written
    assert output_path.exists()
    assert output_path.stat().st_size > 0

    # Verify content structure
    assert "lmm" in report
    assert "random_forest" in report
    assert "sensitivity_reference" in report

    # Verify LMM metrics
    assert "adjusted_r_squared" in report["lmm"]
    assert "rmse" in report["lmm"]
    assert "p_values" in report["lmm"]
    assert "cv_mean_r_squared" in report["lmm"]

    # Verify RF metrics
    assert "r_squared" in report["random_forest"]
    assert "rmse" in report["random_forest"]
    assert "cv_mean_r_squared" in report["random_forest"]

    # Verify values match input
    assert report["lmm"]["adjusted_r_squared"] == 0.75
    assert report["random_forest"]["r_squared"] == 0.68

def test_generate_model_metrics_report_missing_file(temp_dir):
    """Test that FileNotFoundError is raised when input is missing."""
    output_path = temp_dir / "output.json"
    missing_path = temp_dir / "nonexistent.json"

    with pytest.raises(FileNotFoundError):
        generate_model_metrics_report(
            missing_path,
            missing_path,
            output_path
        )

def test_generate_model_metrics_report_missing_metrics(temp_dir):
    """Test that ValueError is raised when required metrics are missing."""
    # Create incomplete model results
    incomplete_data = {
        "lmm": {
            # missing adjusted_r_squared
            "rmse": 1.23
        },
        "random_forest": {
            "r_squared": 0.68,
            "rmse": 1.45,
            "cv_mean_r_squared": 0.65
        }
    }
    model_path = temp_dir / "model_results.json"
    save_json_file(model_path, incomplete_data)

    sensitivity_path = temp_dir / "sensitivity.json"
    save_json_file(sensitivity_path, {"literature_overlap": True})

    output_path = temp_dir / "output.json"

    with pytest.raises(ValueError) as excinfo:
        generate_model_metrics_report(
            model_path,
            sensitivity_path,
            output_path
        )
    assert "adjusted_r_squared" in str(excinfo.value)

def test_report_json_valid(temp_dir, mock_model_results, mock_sensitivity_analysis):
    """Test that the output file is valid JSON."""
    output_path = temp_dir / "model_metrics_raw.json"

    generate_model_metrics_report(
        mock_model_results,
        mock_sensitivity_analysis,
        output_path
    )

    # Re-load and parse to ensure validity
    with open(output_path, 'r', encoding='utf-8') as f:
        parsed = json.load(f)

    assert isinstance(parsed, dict)
    assert "lmm" in parsed
    assert "random_forest" in parsed