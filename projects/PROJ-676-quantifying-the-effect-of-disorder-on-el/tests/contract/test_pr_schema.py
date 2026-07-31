import json
import os
import pytest
from pathlib import Path
from code.config import get_config

def test_localization_length_schema():
    """
    Contract test for PR calculation output schema.
    Asserts output matches localization_length_schema.json.
    """
    config = get_config()
    input_path = Path(config.DATA_DIR) / "processed" / "scaling_fits.json"
    
    if not input_path.exists():
        pytest.skip("scaling_fits.json not generated yet")
    
    with open(input_path, 'r') as f:
        data = json.load(f)
    
    assert isinstance(data, list), "Output must be a list"
    
    required_keys = {"disorder_width", "xi", "uncertainty", "p_value"}
    for item in data:
        assert isinstance(item, dict), "Each item must be a dict"
        assert required_keys.issubset(item.keys()), f"Missing keys: {required_keys - set(item.keys())}"
        assert isinstance(item["disorder_width"], (int, float))
        assert isinstance(item["xi"], (int, float))
        assert isinstance(item["uncertainty"], (int, float))
        assert isinstance(item["p_value"], (int, float))