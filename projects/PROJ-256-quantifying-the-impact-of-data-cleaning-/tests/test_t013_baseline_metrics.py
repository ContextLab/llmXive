"""
Simple sanity test for T013 – ensures that the baseline metrics file is
created and contains at least one dataset entry with the required keys.
"""

import json
from pathlib import Path

def test_baseline_metrics_file_exists():
    path = Path("data/processed/baseline_metrics.json")
    assert path.is_file(), "Baseline metrics JSON was not created."

def test_baseline_metrics_content():
    path = Path("data/processed/baseline_metrics.json")
    with open(path, "r", encoding="utf-8") as fp:
        data = json.load(fp)
    # Expect a list of dicts
    assert isinstance(data, list) and len(data) > 0, "Baseline metrics should contain at least one dataset."
    required = {"dataset_name", "t_test", "regression"}
    for entry in data:
        assert required.issubset(entry.keys()), "Missing required keys in baseline entry."
        # Check numeric precision (three decimal places)
        p_val = entry["t_test"]["p_value"]
        assert isinstance(p_val, float) and round(p_val, 3) == p_val, "p_value not rounded to 3 decimals."

# The test suite will be executed via pytest; no additional boilerplate needed.