"""
Simple unit test that verifies the existence and basic schema of the
``output.json`` produced by the first analysis script.
"""

import json
from pathlib import Path

from config import CONFIG

def test_output_json_exists_and_contains_required_fields():
    output_path = CONFIG.OUTPUT_JSON_PATH
    assert output_path.is_file(), f"Output file missing: {output_path}"

    with open(output_path) as f:
        data = json.load(f)

    # Required top‑level keys for Task T049
    required_keys = {
        "row_count",
        "pearson_r",
        "pearson_p",
        "mae_dft",
        "mae_baseline",
        "r2_ci",
        "mae_ci",
        "fold_metrics",
    }
    missing = required_keys - data.keys()
    assert not missing, f"Missing required keys in output.json: {missing}"

    # Basic sanity checks
    assert isinstance(data["row_count"], int) and data["row_count"] >= 20
    assert isinstance(data["pearson_r"], float)
    assert isinstance(data["mae_dft"], float)
    assert isinstance(data["mae_baseline"], float)      

# The test will be collected by pytest via the normal test discovery.