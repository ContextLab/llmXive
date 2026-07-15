"""
Integration tests for End-to-End Validation.

Verifies that the full pipeline runs successfully on a multi-day interval
and produces all required artifacts (JSON, PNGs).

File path: tests/integration/test_e2e_validation.py
"""
import os
import sys
import json
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import tempfile
import shutil

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from code.main import run_pipeline
from code.config import LAG_WINDOW_MIN, LAG_WINDOW_MAX, LAG_STEP

# Configuration for the test
# Using a short, specific window to minimize API load and execution time
# while still being multi-day (3 days).
SAMPLE_START = datetime(2024, 3, 20, 0, 0, 0)
SAMPLE_END = datetime(2024, 3, 23, 0, 0, 0)

# We will run the pipeline in a temporary directory to avoid polluting the main results
# However, the main.py expects to write to a specific path relative to project root.
# For this test, we assume the standard project structure and write to a temp subfolder
# or mock the output directory if necessary. 
# To strictly follow the "run as is" requirement, we will run it and check the standard location
# but we must ensure the test doesn't fail if the user hasn't run it yet.
# Actually, the task is to run the validation. The test should trigger the run.

RESULTS_DIR = os.path.join(project_root, "data", "processed", "results")

def test_e2e_pipeline_execution():
    """
    Test that the full pipeline executes without error and produces a valid JSON report.
    """
    # Ensure results dir exists
    os.makedirs(RESULTS_DIR, exist_ok=True)
    
    # Run the pipeline
    try:
        report = run_pipeline(SAMPLE_START, SAMPLE_END)
    except Exception as e:
        pytest.fail(f"Pipeline execution failed: {e}")
    
    assert report is not None, "Pipeline returned None"
    
    # Check required keys
    required_keys = [
        "pearson", "spearman", "p_val_permutation", 
        "optimal_lag", "lag_correlation_value",
        "lag_difference", "sensitivity_table", "notes"
    ]
    
    missing = [k for k in required_keys if k not in report]
    assert not missing, f"Report missing keys: {missing}"
    
    # Verify types
    assert isinstance(report["pearson"], (int, float)), "Pearson must be numeric"
    assert isinstance(report["optimal_lag"], (int, float)), "Optimal lag must be numeric"
    assert isinstance(report["sensitivity_table"], list), "Sensitivity table must be a list"

def test_e2e_plot_generation():
    """
    Test that the required PNG plots are generated.
    """
    # Ensure the pipeline has run (or run it if files missing)
    json_path = os.path.join(RESULTS_DIR, "us1_correlation.json")
    if not os.path.exists(json_path):
        run_pipeline(SAMPLE_START, SAMPLE_END)
    
    plots = ["plot_scatter.png", "plot_timeseries.png"]
    for plot in plots:
        path = os.path.join(RESULTS_DIR, plot)
        assert os.path.exists(path), f"Plot {plot} not found in {RESULTS_DIR}"
        assert os.path.getsize(path) > 0, f"Plot {plot} is empty"

def test_e2e_sensitivity_table():
    """
    Test that the sensitivity table contains expected thresholds.
    """
    json_path = os.path.join(RESULTS_DIR, "us1_correlation.json")
    if not os.path.exists(json_path):
        run_pipeline(SAMPLE_START, SAMPLE_END)
    
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    assert "sensitivity_table" in data, "Sensitivity table missing from report"
    
    # Check that we have entries for the expected thresholds (400, 500, 600)
    thresholds = [row.get("threshold_km_s") for row in data["sensitivity_table"]]
    expected_thresholds = [400, 500, 600]
    
    for t in expected_thresholds:
        assert t in thresholds, f"Threshold {t} km/s missing from sensitivity table"
        
    # Verify correlation values are numeric
    for row in data["sensitivity_table"]:
        assert isinstance(row.get("pearson"), (int, float)), "Correlation in sensitivity table must be numeric"
        assert isinstance(row.get("threshold_km_s"), (int, float)), "Threshold must be numeric"
