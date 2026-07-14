import json
from pathlib import Path

import pytest

from t033_outlier_threshold_sweep import main as sweep_main

@pytest.mark.integration
def test_outlier_threshold_sweep_produces_output(tmp_path, monkeypatch):
    """
    Integration test that the sweep script creates the expected JSON file.
    """
    # Run the sweep (uses the real data under data/raw)
    sweep_main()
    result_file = Path("data/processed/outlier_threshold_sweep.json")
    assert result_file.is_file(), "Result JSON was not created"

    # Basic sanity checks on the JSON structure
    with open(result_file) as f:
        data = json.load(f)
    assert isinstance(data, dict) and data, "Result JSON is empty or not a dict"
    for k, metrics in data.items():
        assert "false_positive_rate" in metrics
        assert "inconsistency_rate" in metrics
        # Rates should be 0 or 1 for the simple implementation
        assert metrics["false_positive_rate"] in (0, 1)
        assert metrics["inconsistency_rate"] in (0, 1)