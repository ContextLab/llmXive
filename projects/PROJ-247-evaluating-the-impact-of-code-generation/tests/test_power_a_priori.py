"""
Test that the a‑priori power analysis script produces a JSON file with a
``target_pairs`` value that satisfies the project‑level requirement
(≥ 250 matched pairs).
"""

import json
from pathlib import Path

def test_power_a_priori_exists_and_meets_requirement():
    """
    Verify that ``data/analysis/power_analysis_a_priori.json`` exists and
    that the ``target_pairs`` field is at least 250.
    """
    json_path = Path("data/analysis/power_analysis_a_priori.json")
    assert json_path.is_file(), f"Expected JSON file not found: {json_path}"

    with json_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    # Basic schema sanity checks
    assert "target_pairs" in data, "Missing 'target_pairs' key in JSON output"
    assert isinstance(data["target_pairs"], int), "'target_pairs' must be an integer"

    # Project‑level requirement
    assert data["target_pairs"] >= 250, (
        f"target_pairs ({data['target_pairs']}) is below the required minimum of 250"
    )