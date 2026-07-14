"""
Integration test for baseline analysis pipeline (T010).
Verifies that the baseline analysis script produces `data/processed/baseline_metrics.json`
with valid p-values (0 < p < 1) and finite Confidence Intervals.

This test addresses the execution failure where `t012_run_baseline_analysis.py`
failed to import `load_datasets_from_raw` from `analysis`. It ensures the pipeline
runs end-to-end and produces the required artifact.
"""
import os
import sys
import json
import pytest
import logging
from pathlib import Path

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).parent.parent.parent
CODE_DIR = PROJECT_ROOT / "code"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"

sys.path.insert(0, str(CODE_DIR))
sys.path.insert(0, str(PROJECT_ROOT))

from utils import setup_logging
from data_loader import load_datasets_from_raw
from analysis import run_baseline_analysis
from config import get_config

# Setup logging for the test
logger = setup_logging("INFO")

# Constants for validation
EXPECTED_OUTPUT_FILE = DATA_PROCESSED / "baseline_metrics.json"
REQUIRED_KEYS = ["datasets", "metadata"]
P_VALUE_MIN = 0.0
P_VALUE_MAX = 1.0

def test_baseline_analysis_produces_valid_metrics():
    """
    Integration test:
    1. Ensure raw data exists (or is downloaded).
    2. Run the baseline analysis script logic.
    3. Verify the output file exists.
    4. Verify the JSON structure contains valid p-values and finite CIs.
    """
    
    # 1. Setup: Ensure raw data exists
    # We rely on T011 ensuring data exists, but we check here for robustness.
    if not RAW_DATA_DIR.exists() or not any(RAW_DATA_DIR.iterdir()):
        pytest.skip("Raw data directory is empty. T011 (ensure_data) must run first.")

    # 2. Run Baseline Analysis
    # We call the function directly to simulate the script execution of t012_run_baseline_analysis.py
    # This fixes the import error by using the correct function signature.
    try:
        # Attempt to load datasets from the raw directory
        datasets = load_datasets_from_raw(str(RAW_DATA_DIR))
        
        if not datasets:
            pytest.skip("No datasets found in raw directory to analyze.")

        # Run baseline analysis on the first available dataset to generate the report
        # The run_baseline_analysis function is expected to write to the default output path
        # or we can pass the config to specify it.
        
        config = get_config()
        output_file = str(DATA_PROCESSED / "baseline_metrics.json")
        
        # Ensure output directory exists
        DATA_PROCESSED.mkdir(parents=True, exist_ok=True)

        # Execute the analysis
        # Note: run_baseline_analysis signature varies. We use the one that accepts raw_dir and output_file
        # as per the execution log context, or the dict-returning one if we need to process specific datasets.
        # Given the error log: `from analysis import run_baseline_analysis, load_datasets_from_raw`
        # and the call in t012: `run_baseline_analysis(raw_dir, output_file, config={})`
        # We attempt to call it with those arguments.
        
        success = run_baseline_analysis(str(RAW_DATA_DIR), output_file, config={})
        
        if not success:
            logger.error("Baseline analysis script returned failure.")
            assert False, "Baseline analysis script execution failed."

    except ImportError as e:
        pytest.fail(f"Import error during baseline analysis execution: {e}")
    except Exception as e:
        pytest.fail(f"Runtime error during baseline analysis: {e}")

    # 3. Verify Output File Exists
    assert EXPECTED_OUTPUT_FILE.exists(), f"Output file {EXPECTED_OUTPUT_FILE} was not created."

    # 4. Validate JSON Content
    with open(EXPECTED_OUTPUT_FILE, 'r') as f:
        data = json.load(f)

    # Check top-level keys
    assert "datasets" in data, "Missing 'datasets' key in baseline_metrics.json"
    assert isinstance(data["datasets"], list), "'datasets' must be a list"
    
    assert len(data["datasets"]) > 0, "No datasets were recorded in baseline_metrics.json"

    # Validate each dataset entry
    for dataset_entry in data["datasets"]:
        dataset_name = dataset_entry.get("dataset_name", "Unknown")
        logger.info(f"Validating metrics for dataset: {dataset_name}")

        # Check for analysis results
        if "analysis" not in dataset_entry:
            continue # Skip if no analysis was performed (e.g., no numerical columns)

        analysis = dataset_entry["analysis"]

        # Check t-tests
        if "t_tests" in analysis:
            for test_name, test_result in analysis["t_tests"].items():
                p_val = test_result.get("p_value")
                ci = test_result.get("ci")

                # Validate P-value
                assert p_val is not None, f"P-value missing for {test_name} in {dataset_name}"
                assert P_VALUE_MIN < p_val < P_VALUE_MAX, \
                    f"P-value {p_val} for {test_name} in {dataset_name} is out of range (0, 1)"

                # Validate CI
                if ci:
                    assert len(ci) == 2, f"CI for {test_name} in {dataset_name} must have 2 bounds"
                    lower, upper = ci
                    assert float(lower) != float('inf') and float(lower) != float('-inf'), \
                        f"Lower CI bound for {test_name} in {dataset_name} is infinite"
                    assert float(upper) != float('inf') and float(upper) != float('-inf'), \
                        f"Upper CI bound for {test_name} in {dataset_name} is infinite"

        # Check linear regressions
        if "linear_regressions" in analysis:
            for model_name, model_result in analysis["linear_regressions"].items():
                p_val = model_result.get("p_value")
                ci = model_result.get("ci")

                if p_val is not None:
                    assert P_VALUE_MIN < p_val < P_VALUE_MAX, \
                        f"P-value {p_val} for {model_name} in {dataset_name} is out of range (0, 1)"

                if ci:
                    assert len(ci) == 2, f"CI for {model_name} in {dataset_name} must have 2 bounds"
                    lower, upper = ci
                    assert float(lower) != float('inf') and float(lower) != float('-inf'), \
                        f"Lower CI bound for {model_name} in {dataset_name} is infinite"
                    assert float(upper) != float('inf') and float(upper) != float('-inf'), \
                        f"Upper CI bound for {model_name} in {dataset_name} is infinite"

    logger.info("Integration test PASSED: baseline_metrics.json is valid.")