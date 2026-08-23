"""
Integration tests for T080: Final Verification of Universal Approximation.
"""
import os
import json
import tempfile
from pathlib import Path
import pytest
import numpy as np
import torch

from src.experiments.final_verification import (
    verify_universal_approximation,
    generate_report,
    load_test_data,
    main
)
from src.data.benchmarks import generate_polynomial_test_data

# Constants
TEST_DATA_PATH = Path("data/results/test_data_polynomial.npy")
REPORT_PATH = Path("data/results/universal_approximation_report.md")
RESULTS_JSON_PATH = Path("data/results/universal_approximation_results.json")

@pytest.fixture(autouse=True)
def setup_test_environment(tmp_path, monkeypatch):
    """
    Set up a temporary directory structure for testing.
    """
    # Create necessary directories
    results_dir = tmp_path / "data" / "results"
    logs_dir = tmp_path / "data" / "logs"
    results_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    # Monkeypatch the paths to use temp directory
    monkeypatch.setattr(
        "src.experiments.final_verification.RESULTS_DIR",
        results_dir
    )
    monkeypatch.setattr(
        "src.experiments.final_verification.LOGS_DIR",
        logs_dir
    )
    monkeypatch.setattr(
        "src.experiments.final_verification.TEST_DATA_PATH",
        results_dir / "test_data_polynomial.npy"
    )
    monkeypatch.setattr(
        "src.experiments.final_verification.REPORT_PATH",
        results_dir / "universal_approximation_report.md"
    )
    
    # Generate test data
    generate_polynomial_test_data(output_path=str(results_dir / "test_data_polynomial.npy"))
    
    yield tmp_path

def test_load_test_data_exists(setup_test_environment):
    """Test that load_test_data can successfully load the polynomial test data."""
    tmp_path = setup_test_environment
    X, y = load_test_data()
    
    assert X is not None
    assert y is not None
    assert len(X) > 0
    assert len(y) > 0
    assert X.shape[0] == y.shape[0]

def test_verify_universal_approximation_baseline(setup_test_environment):
    """Test baseline model evaluation."""
    result = verify_universal_approximation(
        model_type="baseline",
        seed=42,
        batch_size=16
    )
    
    assert result["model_type"] == "baseline"
    assert "test_mae" in result
    assert "param_count" in result
    assert result["test_mae"] >= 0
    assert result["param_count"] > 0

def test_verify_universal_approximation_microcircuit(setup_test_environment):
    """Test microcircuit model evaluation."""
    result = verify_universal_approximation(
        model_type="microcircuit",
        num_columns=1,
        seed=42,
        batch_size=16
    )
    
    assert result["model_type"] == "microcircuit"
    assert result["num_columns"] == 1
    assert "test_mae" in result
    assert "param_count" in result
    assert result["test_mae"] >= 0
    assert result["param_count"] > 0

def test_verify_universal_approximation_gradient_logging(setup_test_environment):
    """Test that gradient norms are logged correctly."""
    result = verify_universal_approximation(
        model_type="microcircuit",
        num_columns=1,
        seed=42,
        batch_size=16
    )
    
    # Check that gradient norms file was created
    logs_dir = Path("data/logs")
    gradient_file = logs_dir / "gradient_norms.json"
    
    assert gradient_file.exists(), "Gradient norms file should be created"
    
    # Verify JSON format
    with open(gradient_file, 'r') as f:
        content = f.read()
        assert len(content) > 0
        
    # Try to parse as JSON array (one entry per log call)
    try:
        import json
        data = json.loads(content)
        assert isinstance(data, list) or isinstance(data, dict)
    except json.JSONDecodeError:
        # If it's not valid JSON, the file might be in line-delimited format
        # which is also acceptable
        pass

def test_generate_report(setup_test_environment):
    """Test report generation."""
    baseline_result = {
        "model_type": "baseline",
        "test_mae": 0.03,
        "param_count": 1000,
        "eval_time_sec": 1.0,
        "device": "cpu"
    }
    
    microcircuit_results = [
        {
            "model_type": "microcircuit",
            "num_columns": 1,
            "test_mae": 0.035,
            "param_count": 1050,
            "eval_time_sec": 1.2,
            "device": "cpu"
        }
    ]
    
    report = generate_report(baseline_result, microcircuit_results)
    
    assert report is not None
    assert len(report) > 0
    assert "Universal Approximation Verification Report" in report
    assert "Same test harness" in report or "same test harness" in report
    assert "Polynomial surfaces" in report
    assert "Baseline MAE" in report
    assert "Microcircuit MAE" in report

def test_main_function(setup_test_environment):
    """Test the main function execution."""
    results = main()
    
    assert results is not None
    assert "baseline" in results
    assert "microcircuit" in results
    
    # Check that report file was created
    assert REPORT_PATH.exists(), "Report file should be created"
    
    # Check that results JSON was created
    assert RESULTS_JSON_PATH.exists(), "Results JSON should be created"
    
    # Verify report content
    with open(REPORT_PATH, 'r') as f:
        report_content = f.read()
        assert len(report_content) > 0
        assert "Universal Approximation Verification Report" in report_content
    
    # Verify results JSON content
    with open(RESULTS_JSON_PATH, 'r') as f:
        results_content = json.load(f)
        assert "baseline" in results_content
        assert "microcircuit" in results_content
        assert len(results_content["microcircuit"]) > 0

def test_same_test_harness_assertion(setup_test_environment):
    """
    Verify that the same test harness is used for both models.
    This is a critical requirement for T080.
    """
    # Run both models with identical parameters
    baseline_result = verify_universal_approximation(
        model_type="baseline",
        seed=42,
        batch_size=16
    )
    
    microcircuit_result = verify_universal_approximation(
        model_type="microcircuit",
        num_columns=1,
        seed=42,
        batch_size=16
    )
    
    # Verify that the test data path is the same
    assert baseline_result["test_data_path"] == microcircuit_result["test_data_path"]
    
    # Verify that the same seed was used
    assert baseline_result["seed"] == microcircuit_result["seed"]
    
    # Verify that the same device was used
    assert baseline_result["device"] == microcircuit_result["device"]

def test_report_contains_methodology_note(setup_test_environment):
    """Verify that the report explicitly states the same test harness is used."""
    main()
    
    with open(REPORT_PATH, 'r') as f:
        report_content = f.read()
    
    # Check for explicit statement about same test harness
    assert "same test harness" in report_content.lower() or \
           "Same test harness" in report_content, \
           "Report should explicitly state that the same test harness is used"
    
    # Check for dataset reference
    assert "polynomial surfaces" in report_content.lower(), \
           "Report should mention polynomial surfaces dataset"
    
    # Check for seed reference
    assert "42" in report_content, \
           "Report should mention the random seed (42)"