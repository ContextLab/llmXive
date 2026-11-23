import json
import os
import pytest
from pathlib import Path
from code.config import get_config

def test_lyapunov_exponents_schema():
    """
    Contract test for TM output schema.
    """
    config = get_config()
    input_path = Path(config.DATA_DIR) / "processed" / "lyapunov_exponents.json"
    
    if not input_path.exists():
        pytest.skip("lyapunov_exponents.json not generated yet")
    
    with open(input_path, 'r') as f:
        data = json.load(f)
    
    assert isinstance(data, list), "Output must be a list"
    
    required_keys = {"disorder_width", "realization_index", "lyapunov_exponent", "localization_length"}
    for item in data:
        assert isinstance(item, dict), "Each item must be a dict"
        assert required_keys.issubset(item.keys()), f"Missing keys: {required_keys - set(item.keys())}"
