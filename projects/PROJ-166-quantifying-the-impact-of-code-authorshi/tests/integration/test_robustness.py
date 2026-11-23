"""
Integration test for User Story 3: Robustness Checks and Sensitivity Analysis.

This test verifies the complete execution of the robustness analysis pipeline,
including:
1. Subsampling by language
2. Shannon Entropy alternative metric
3. Lagged variable analysis
4. Interaction terms analysis

It asserts that all expected output files are generated and contain valid data
structures as per the specification.
"""
import os
import sys
import json
import logging
import pandas as pd
from pathlib import Path
from typing import Dict, Any

# Add project root to path to allow imports from code/
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from analysis.robustness import main as run_robustness_main
from analysis.fit_models import main as run_fit_models_main
from config import ensure_directories

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Expected output paths
EXPECTED_OUTPUTS = {
    "subsample_pvalues": "data/processed/robustness_subsample_pvalues.csv",
    "entropy_pvalues": "data/processed/robustness_entropy_pvalues.csv",
    "lagged_results": "data/processed/robustness_lagged_results.json",
    "interaction_pvalues": "data/processed/robustness_interaction_pvalues.csv",
    "final_robustness_json": "data/processed/robustness_results.json",
}

def test_subsample_analysis():
    """Test that subsampling by language produces valid CSV output."""
    output_path = EXPECTED_OUTPUTS["subsample_pvalues"]
    assert os.path.exists(output_path), f"Subsample output file missing: {output_path}"
    
    df = pd.read_csv(output_path)
    required_columns = ["language", "coefficient", "std_err", "p_value_raw", "n_rows"]
    assert all(col in df.columns for col in required_columns), \
        f"Subsample CSV missing required columns. Found: {df.columns.tolist()}"
    
    # Check that at least one language was processed (n_rows > 0)
    assert df["n_rows"].sum() > 0, "No valid subsamples were processed."
    logger.info(f"Subsample test passed: {len(df)} language groups analyzed.")

def test_entropy_analysis():
    """Test that entropy-based GLM produces valid CSV output."""
    output_path = EXPECTED_OUTPUTS["entropy_pvalues"]
    assert os.path.exists(output_path), f"Entropy output file missing: {output_path}"
    
    df = pd.read_csv(output_path)
    required_columns = ["model_type", "coefficient", "std_err", "p_value_raw", "coefficient_diff"]
    assert all(col in df.columns for col in required_columns), \
        f"Entropy CSV missing required columns. Found: {df.columns.tolist()}"
    
    assert len(df) > 0, "Entropy model produced no results."
    logger.info("Entropy test passed.")

def test_lagged_analysis():
    """Test that lagged variable analysis produces valid JSON output."""
    output_path = EXPECTED_OUTPUTS["lagged_results"]
    assert os.path.exists(output_path), f"Lagged output file missing: {output_path}"
    
    with open(output_path, "r") as f:
        data = json.load(f)
    
    # Verify structure based on T034 spec
    assert "coefficients" in data or "results" in data, \
        "Lagged JSON missing 'coefficients' or 'results' key."
    assert "excluded_repos" in data or "exclusion_reason" in data, \
        "Lagged JSON missing exclusion metadata."
    
    logger.info("Lagged analysis test passed.")

def test_interaction_analysis():
    """Test that interaction terms analysis produces valid CSV output."""
    output_path = EXPECTED_OUTPUTS["interaction_pvalues"]
    assert os.path.exists(output_path), f"Interaction output file missing: {output_path}"
    
    df = pd.read_csv(output_path)
    required_columns = ["interaction_term", "coefficient", "std_err", "p_value_raw"]
    assert all(col in df.columns for col in required_columns), \
        f"Interaction CSV missing required columns. Found: {df.columns.tolist()}"
    
    assert len(df) > 0, "Interaction model produced no results."
    logger.info("Interaction test passed.")

def test_final_robustness_json():
    """Test that the final aggregated robustness JSON is valid."""
    output_path = EXPECTED_OUTPUTS["final_robustness_json"]
    assert os.path.exists(output_path), f"Final robustness JSON missing: {output_path}"
    
    with open(output_path, "r") as f:
        data = json.load(f)
    
    # Verify it contains the aggregated results
    assert "subsample" in data or "entropy" in data or "lagged" in data or "interaction" in data, \
        "Final JSON missing robustness sections."
    assert "adjusted_p_values" in data or "bh_correction" in data, \
        "Final JSON missing adjusted p-values."
    
    logger.info("Final robustness JSON test passed.")

def test_full_robustness_pipeline():
    """
    End-to-end integration test: Run the robustness pipeline and verify all outputs.
    This test assumes T017 (fit_models.py) has already generated model_results_raw.json.
    """
    # Ensure directories exist
    ensure_directories()
    
    input_file = "data/processed/repo_metrics_clean.csv"
    if not os.path.exists(input_file):
        logger.error(f"Input file missing: {input_file}. "
                     "Please run T009 (merge_datasets.py) first.")
        raise FileNotFoundError(f"Required input {input_file} not found.")

    # Run the robustness main logic
    # Note: In a real CI, we might need to mock the fit_models step if it hasn't run,
    # but here we assume the pipeline state is consistent.
    try:
        run_robustness_main()
    except Exception as e:
        logger.error(f"Robustness pipeline execution failed: {e}")
        raise

    # Verify all expected outputs
    test_subsample_analysis()
    test_entropy_analysis()
    test_lagged_analysis()
    test_interaction_analysis()
    test_final_robustness_json()

    logger.info("All robustness integration tests passed successfully.")

if __name__ == "__main__":
    test_full_robustness_pipeline()