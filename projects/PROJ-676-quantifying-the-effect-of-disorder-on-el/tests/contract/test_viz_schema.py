import json
import os
import pytest
from pathlib import Path
from code.config import get_config

def test_visualization_output_format():
    """
    Contract test for visualization output format.
    """
    config = get_config()
    input_path = Path(config.DATA_DIR) / "processed" / "fit_results.json"
    
    if not input_path.exists():
        pytest.skip("fit_results.json not generated yet")
    
    with open(input_path, 'r') as f:
        data = json.load(f)
    
    assert isinstance(data, list), "Output must be a list"
    
    required_keys = {"decay_length", "R_squared", "site_index"}
    for item in data:
        assert isinstance(item, dict), "Each item must be a dict"
        assert required_keys.issubset(item.keys()), f"Missing keys: {required_keys - set(item.keys())}"
