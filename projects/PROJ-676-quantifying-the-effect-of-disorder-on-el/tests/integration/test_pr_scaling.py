"""
Integration test for finite-size scaling workflow.
Tests T011.
"""
import json
import os
import pytest
from pathlib import Path
from code.analyze_pr import run_scaling_analysis
from code.config import get_config

def test_scaling_fits_output_exists():
    """
    Asserts existence of data/processed/scaling_fits.json with schema validation.
    """
    # Run the analysis first to generate the file
    config = get_config()
    # Ensure we have valid config
    if not config.get("W_LIST") or not config.get("L_LIST"):
        config["W_LIST"] = [0.5, 1.0]
        config["L_LIST"] = [100, 200]
        config["NUM_REALIZATIONS"] = 5
        config["SEED"] = 42

    run_scaling_analysis(config)

    output_path = Path("data/processed/scaling_fits.json")
    assert output_path.exists(), f"File {output_path} does not exist"

    with open(output_path, 'r') as f:
        data = json.load(f)

    assert isinstance(data, list), "Output must be a list"

    if len(data) > 0:
        item = data[0]
        assert "xi" in item, "Key 'xi' must be present"
        assert "uncertainty" in item, "Key 'uncertainty' must be present"
        assert "disorder_width" in item, "Key 'disorder_width' must be present"

        assert isinstance(item["xi"], (int, float)), "xi must be numeric"
        assert isinstance(item["uncertainty"], (int, float)), "uncertainty must be numeric"
        assert isinstance(item["disorder_width"], (int, float)), "disorder_width must be numeric"

        assert item["xi"] is not None, "xi must not be null"
        assert item["uncertainty"] is not None, "uncertainty must not be null"
        assert item["disorder_width"] is not None, "disorder_width must not be null"

def test_scaling_fits_schema_compliance():
    """
    Validates the schema of scaling_fits.json against expected structure.
    """
    output_path = Path("data/processed/scaling_fits.json")
    if not output_path.exists():
        pytest.skip("scaling_fits.json not generated yet")

    with open(output_path, 'r') as f:
        data = json.load(f)

    for item in data:
        required_keys = ["xi", "uncertainty", "disorder_width"]
        for key in required_keys:
            assert key in item, f"Missing required key: {key}"
            assert item[key] is not None, f"Key {key} is null"
            assert isinstance(item[key], (int, float)), f"Key {key} must be numeric"
