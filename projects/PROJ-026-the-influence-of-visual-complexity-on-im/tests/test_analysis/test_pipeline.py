"""
Integration test for the full analysis pipeline (T031).

This test verifies that the entire analysis pipeline (PCA -> Permutation Test -> 
Sensitivity Analysis -> Results Saving) produces the expected output files with
the correct structure and keys.

The test uses the --null-effect flag to generate synthetic data for CI purposes,
ensuring the pipeline runs end-to-end without requiring real experimental data.
"""
import os
import sys
import json
import pytest
from pathlib import Path
import pandas as pd
import numpy as np

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from config import get_project_root, ensure_directories, get_data_path
from utils.logging import setup_logging, get_logger


@pytest.fixture(autouse=True)
def setup_test_environment(tmp_path):
    """Set up a temporary project structure for the test."""
    # Create a temporary directory structure mimicking the project
    temp_root = tmp_path / "test_project"
    temp_root.mkdir()
    
    # Create required directories
    dirs = [
        "code/data", "code/stimuli", "code/analysis", "code/viz", "code/utils",
        "data/raw/stimuli", "data/raw/responses", "data/processed", "data/results",
        "logs", "docs"
    ]
    for d in dirs:
        (temp_root / d).mkdir(parents=True, exist_ok=True)
    
    # Set environment variable to point to temp root
    os.environ["PROJECT_ROOT"] = str(temp_root)
    
    # Setup logging to temp directory
    setup_logging(log_level="INFO", log_dir=str(temp_root / "logs"))
    
    yield temp_root
    
    # Cleanup
    del os.environ["PROJECT_ROOT"]


def test_full_analysis_pipeline(setup_test_environment):
    """
    Integration test for the full analysis pipeline.
    
    This test:
    1. Generates synthetic data (using --null-effect mode)
    2. Runs the full pipeline (PCA, Permutation Test, Sensitivity Analysis)
    3. Verifies that output files exist and contain expected keys
    
    Expected output files:
    - data/results/pca_variance.json
    - data/results/permutation_results.json
    - data/results/sensitivity_results.json
    - data/results/power_analysis.json
    """
    temp_root = setup_test_environment
    code_root = temp_root / "code"
    data_root = temp_root / "data"
    results_root = data_root / "results"
    
    # Ensure the main.py script can be imported
    sys.path.insert(0, str(code_root))
    
    # Mock the data generation step by creating minimal required input files
    logger = get_logger("test_pipeline")
    logger.info("Creating minimal synthetic input data for pipeline test")
    
    # Create minimal complexity_scores.csv (required for PCA)
    complexity_data = {
        "filename": ["img1.png", "img2.png", "img3.png", "img4.png"],
        "edge_density": [0.1, 0.5, 0.8, 0.3],
        "entropy": [0.2, 0.6, 0.9, 0.4],
        "fractal_dim": [1.5, 2.0, 2.5, 1.8],
        "complexity_category": ["Low", "High", "High", "Low"]
    }
    complexity_df = pd.DataFrame(complexity_data)
    complexity_path = data_root / "processed" / "complexity_scores.csv"
    complexity_df.to_csv(complexity_path, index=False)
    logger.info(f"Created {complexity_path}")
    
    # Create minimal aggregated_d_scores.csv (required for permutation test)
    d_scores_data = {
        "participant_id": ["P001", "P002", "P003", "P004", "P005", "P006"],
        "session_id": ["S1", "S1", "S1", "S2", "S2", "S2"],
        "complexity_condition": ["Low", "Low", "Low", "High", "High", "High"],
        "d_score": [0.5, 0.6, 0.4, 0.3, 0.2, 0.35],
        "n_trials_valid": [50, 50, 50, 50, 50, 50],
        "status": ["valid", "valid", "valid", "valid", "valid", "valid"]
    }
    d_scores_df = pd.DataFrame(d_scores_data)
    d_scores_path = data_root / "processed" / "aggregated_d_scores.csv"
    d_scores_df.to_csv(d_scores_path, index=False)
    logger.info(f"Created {d_scores_path}")
    
    # Create minimal counterbalance_assignment.csv (required for joining)
    counterbalance_data = {
        "participant_id": ["P001", "P002", "P003", "P004", "P005", "P006"],
        "session_order": ["Low-High", "Low-High", "Low-High", "High-Low", "High-Low", "High-Low"]
    }
    counterbalance_df = pd.DataFrame(counterbalance_data)
    counterbalance_path = data_root / "processed" / "counterbalance_assignment.csv"
    counterbalance_df.to_csv(counterbalance_path, index=False)
    logger.info(f"Created {counterbalance_path}")
    
    # Now run the pipeline components directly (bypassing CLI for testability)
    logger.info("Running PCA dimensionality check")
    from analysis.pca import run_pca_check
    pca_results = run_pca_check(str(complexity_path), str(results_root))
    assert pca_results is not None, "PCA check should return results"
    assert "cumulative_variance" in pca_results, "PCA results should contain cumulative_variance"
    assert "status" in pca_results, "PCA results should contain status"
    
    # Verify PCA output file exists
    pca_output_path = results_root / "pca_variance.json"
    assert pca_output_path.exists(), f"PCA output file {pca_output_path} should exist"
    
    logger.info("Running Permutation Test")
    from analysis.permutation import run_permutation_test, calculate_effect_size
    permutation_results = run_permutation_test(
        str(d_scores_path), 
        n_permutations=100,  # Reduced for faster CI testing
        seed=42
    )
    assert permutation_results is not None, "Permutation test should return results"
    assert "p_value" in permutation_results, "Permutation results should contain p_value"
    assert "observed_difference" in permutation_results, "Permutation results should contain observed_difference"
    
    logger.info("Calculating effect sizes")
    effect_size_results = calculate_effect_size(
        str(d_scores_path),
        permutation_results["observed_difference"]
    )
    assert effect_size_results is not None, "Effect size calculation should return results"
    assert "effect_size" in effect_size_results, "Effect size results should contain effect_size"
    assert "partial_eta2" in effect_size_results, "Effect size results should contain partial_eta2"
    
    logger.info("Running Sensitivity Analysis")
    from analysis.sensitivity import run_sensitivity_analysis
    sensitivity_results = run_sensitivity_analysis(
        str(complexity_path),
        str(d_scores_path),
        str(results_root),
        n_permutations=50  # Reduced for faster CI testing
    )
    assert sensitivity_results is not None, "Sensitivity analysis should return results"
    assert "threshold_sweep" in sensitivity_results, "Sensitivity results should contain threshold_sweep"
    assert "loio_results" in sensitivity_results, "Sensitivity results should contain loio_results"
    
    logger.info("Running Post-Hoc Power Analysis")
    from analysis.permutation import run_post_hoc_power_analysis
    power_results = run_post_hoc_power_analysis(
        str(d_scores_path),
        target_effect_size=0.02,
        n_participants=60
    )
    assert power_results is not None, "Power analysis should return results"
    assert "power_value" in power_results, "Power results should contain power_value"
    assert "status" in power_results, "Power results should contain status"
    
    # Aggregate and save all results
    logger.info("Saving aggregated results")
    from analysis.results import save_json_results, aggregate_permutation_results
    
    combined_results = aggregate_permutation_results(
        permutation_results,
        effect_size_results,
        sensitivity_results,
        power_results
    )
    
    save_json_results(combined_results, str(results_root / "permutation_results.json"))
    save_json_results(
        {"threshold_sweep": sensitivity_results["threshold_sweep"], 
         "loio_results": sensitivity_results["loio_results"]},
        str(results_root / "sensitivity_results.json")
    )
    save_json_results(power_results, str(results_root / "power_analysis.json"))
    
    # VERIFICATION: Check that all expected output files exist and contain expected keys
    logger.info("Verifying output files")
    
    # 1. Verify pca_variance.json
    assert (results_root / "pca_variance.json").exists(), "pca_variance.json must exist"
    with open(results_root / "pca_variance.json", "r") as f:
        pca_data = json.load(f)
    assert "cumulative_variance" in pca_data, "pca_variance.json must contain cumulative_variance"
    assert "status" in pca_data, "pca_variance.json must contain status"
    
    # 2. Verify permutation_results.json
    assert (results_root / "permutation_results.json").exists(), "permutation_results.json must exist"
    with open(results_root / "permutation_results.json", "r") as f:
        perm_data = json.load(f)
    assert "p_value" in perm_data, "permutation_results.json must contain p_value"
    assert "effect_size" in perm_data, "permutation_results.json must contain effect_size"
    assert "partial_eta2" in perm_data, "permutation_results.json must contain partial_eta2"
    assert "observed_cohen_d" in perm_data, "permutation_results.json must contain observed_cohen_d"
    assert "sensitivity_sweep" in perm_data, "permutation_results.json must contain sensitivity_sweep"
    assert "loio_results" in perm_data, "permutation_results.json must contain loio_results"
    
    # 3. Verify sensitivity_results.json
    assert (results_root / "sensitivity_results.json").exists(), "sensitivity_results.json must exist"
    with open(results_root / "sensitivity_results.json", "r") as f:
        sens_data = json.load(f)
    assert "threshold_sweep" in sens_data, "sensitivity_results.json must contain threshold_sweep"
    assert "loio_results" in sens_data, "sensitivity_results.json must contain loio_results"
    
    # 4. Verify power_analysis.json
    assert (results_root / "power_analysis.json").exists(), "power_analysis.json must exist"
    with open(results_root / "power_analysis.json", "r") as f:
        power_data = json.load(f)
    assert "power_value" in power_data, "power_analysis.json must contain power_value"
    assert "target" in power_data, "power_analysis.json must contain target"
    assert "status" in power_data, "power_analysis.json must contain status"
    
    logger.info("All output files verified successfully!")
    assert True, "Full analysis pipeline integration test passed"