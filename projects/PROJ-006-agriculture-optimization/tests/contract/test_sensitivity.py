"""
Contract test skeleton for sensitivity output (TDD).

This test validates that the sensitivity analysis results conform to the
expected output structure (CSV and JSON metrics).

Note: This test will fail until T030 and T035a are implemented.
"""
import os
import pytest
from pathlib import Path
import pandas as pd
import json

PROJECT_ROOT = Path(__file__).parent.parent.parent
RESULTS_CSV = PROJECT_ROOT / "data" / "processed" / "sensitivity_results.csv"
METRICS_JSON = PROJECT_ROOT / "data" / "processed" / "sensitivity_metrics.json"

@pytest.mark.contract
def test_sensitivity_csv_exists():
    """Assert that sensitivity results CSV exists."""
    assert RESULTS_CSV.exists(), f"Sensitivity results CSV missing: {RESULTS_CSV}"

@pytest.mark.contract
def test_sensitivity_csv_has_required_columns():
    """Assert that sensitivity CSV contains required columns."""
    if not RESULTS_CSV.exists():
        pytest.skip("CSV not found")
    
    df = pd.read_csv(RESULTS_CSV)
    required = ['threshold', 'coefficient_csa_index_model1', 'coefficient_csa_index_model2']
    missing = [c for c in required if c not in df.columns]
    assert not missing, f"CSV missing columns: {missing}"

@pytest.mark.contract
def test_sensitivity_metrics_json_exists():
    """Assert that sensitivity metrics JSON exists."""
    assert METRICS_JSON.exists(), f"Sensitivity metrics JSON missing: {METRICS_JSON}"

@pytest.mark.contract
def test_sensitivity_metrics_has_required_fields():
    """Assert that metrics JSON contains required fields."""
    if not METRICS_JSON.exists():
        pytest.skip("Metrics JSON not found")
    
    with open(METRICS_JSON, 'r') as f:
        data = json.load(f)
    
    required = ['max_delta_coefficient', 'std_coefficient']
    missing = [k for k in required if k not in data]
    assert not missing, f"Metrics JSON missing keys: {missing}"
