"""
Integration test for baseline analysis (T010).
Verifies that the baseline analysis script produces valid output with correct p-values and CIs.
"""
import os
import sys
import json
import pytest
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils import setup_logging
from t012_run_baseline_analysis import main as run_baseline_main
from t013_record_baseline_metrics import main as record_metrics_main

logger = setup_logging("INFO")

BASELINE_RAW_FILE = "data/processed/baseline_raw_output.json"
BASELINE_FINAL_FILE = "data/processed/baseline_metrics.json"

@pytest.fixture(autouse=True)
def setup_environment():
    """Ensure data directories exist."""
    os.makedirs("data/processed", exist_ok=True)
    yield
    # Cleanup optional: remove generated files after test if desired
    # if os.path.exists(BASELINE_RAW_FILE):
    #     os.remove(BASELINE_RAW_FILE)

def test_baseline_pipeline_execution():
    """
    Run the full baseline pipeline (T012 -> T013) and verify artifacts exist.
    """
    # 1. Run T012 (Baseline Analysis)
    logger.info("Running T012 (Baseline Analysis)...")
    exit_code_12 = run_baseline_main()
    assert exit_code_12 == 0, f"T012 failed with exit code {exit_code_12}"
    assert os.path.exists(BASELINE_RAW_FILE), f"T012 did not produce {BASELINE_RAW_FILE}"

    # 2. Run T013 (Record Metrics)
    logger.info("Running T013 (Record Metrics)...")
    exit_code_13 = record_metrics_main()
    assert exit_code_13 == 0, f"T013 failed with exit code {exit_code_13}"
    assert os.path.exists(BASELINE_FINAL_FILE), f"T013 did not produce {BASELINE_FINAL_FILE}"

def test_baseline_metrics_content():
    """
    Verify the content of baseline_metrics.json:
    - Valid JSON structure
    - P-values in (0, 1)
    - Finite CI bounds
    - Effect sizes present
    """
    if not os.path.exists(BASELINE_FINAL_FILE):
        pytest.skip("Baseline metrics file not found. Run T012 and T013 first.")

    with open(BASELINE_FINAL_FILE, 'r') as f:
        data = json.load(f)

    assert 'datasets' in data, "Missing 'datasets' key in baseline_metrics.json"
    assert len(data['datasets']) > 0, "No datasets recorded in baseline_metrics.json"

    for entry in data['datasets']:
        ds_name = entry.get('dataset_name', 'Unknown')
        
        # Check P-value
        p_val = entry.get('p_value')
        assert p_val is not None, f"P-value missing for {ds_name}"
        assert 0 < p_val < 1, f"P-value {p_val} for {ds_name} is not in (0, 1)"
        
        # Check CIs
        ci_lower = entry.get('ci_lower')
        ci_upper = entry.get('ci_upper')
        assert ci_lower is not None and ci_upper is not None, f"CI bounds missing for {ds_name}"
        assert ci_lower != float('inf') and ci_lower != float('-inf'), f"CI lower infinite for {ds_name}"
        assert ci_upper != float('inf') and ci_upper != float('-inf'), f"CI upper infinite for {ds_name}"
        assert ci_lower < ci_upper, f"CI bounds inverted for {ds_name}"
        
        # Check Effect Size
        eff_size = entry.get('effect_size')
        assert eff_size is not None, f"Effect size missing for {ds_name}"
        
        logger.debug(f"Validated {ds_name}: p={p_val}, CI=({ci_lower}, {ci_upper}), ES={eff_size}")

def test_precision_requirement():
    """
    Verify that metrics are recorded with at least 3 decimal precision.
    """
    if not os.path.exists(BASELINE_FINAL_FILE):
        pytest.skip("Baseline metrics file not found.")

    with open(BASELINE_FINAL_FILE, 'r') as f:
        data = json.load(f)

    for entry in data['datasets']:
        p_val = entry.get('p_value')
        # Convert to string and check decimal places (simple check)
        # Note: JSON might strip trailing zeros, so we check the value itself
        # If rounded to 3 decimals, the difference between value and round(value, 3) should be 0
        assert p_val == round(p_val, 3), f"P-value {p_val} for {entry['dataset_name']} lacks 3 decimal precision"
        
        ci_lower = entry.get('ci_lower')
        assert ci_lower == round(ci_lower, 3), f"CI lower {ci_lower} for {entry['dataset_name']} lacks 3 decimal precision"