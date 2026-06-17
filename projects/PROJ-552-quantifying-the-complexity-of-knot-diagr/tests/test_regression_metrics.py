"""
Simple integration test to ensure that the regression metrics JSON file is
produced and contains the expected keys.
"""

import json
from pathlib import Path

def test_regression_metrics_file_exists_and_valid():
    metrics_path = Path("data/analysis/regression_metrics.json")
    assert metrics_path.is_file(), "Regression metrics JSON was not created"
    with metrics_path.open() as f:
        data = json.load(f)
    # Expect at least the linear model entry.
    assert "linear" in data, "Linear model metrics missing"
    # Basic sanity checks on numeric values.
    for metric in ("mae", "r2", "aic", "bic"):
        assert metric in data["linear"], f"{metric} missing in linear model"