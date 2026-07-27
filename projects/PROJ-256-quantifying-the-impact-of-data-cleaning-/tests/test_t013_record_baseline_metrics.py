import json
import os
import sys
from pathlib import Path

import pytest

# Ensure the project root is on PYTHONPATH for imports
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from t013_record_baseline_metrics import main as record_main

@pytest.fixture(scope="module")
def baseline_file():
    # Run the script once to generate the file
    record_main()
    return Path("data/processed/baseline_metrics.json")

def test_baseline_file_exists(baseline_file):
    assert baseline_file.exists(), "baseline_metrics.json should be created"

def test_baseline_content_not_empty(baseline_file):
    with open(baseline_file) as f:
        data = json.load(f)
    assert isinstance(data, dict) and len(data) > 0, "File must contain at least one dataset's metrics"

def test_numeric_precision(baseline_file):
    with open(baseline_file) as f:
        data = json.load(f)
    for ds, metrics in data.items():
        # Check t_test values
        t = metrics["t_test"]
        assert round(t["p_value"], 3) == t["p_value"]
        assert round(t["ci"][0], 3) == t["ci"][0]
        assert round(t["ci"][1], 3) == t["ci"][1]
        # Check linear regression values
        lr = metrics["linear_regression"]
        assert round(lr["p_value"], 3) == lr["p_value"]
        assert round(lr["r_squared"], 3) == lr["r_squared"]
        for ci_vals in lr["ci"].values():
            assert round(ci_vals[0], 3) == ci_vals[0]
            assert round(ci_vals[1], 3) == ci_vals[1]