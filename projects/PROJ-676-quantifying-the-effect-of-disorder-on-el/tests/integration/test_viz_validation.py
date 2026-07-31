import json
import os
import pytest
from pathlib import Path
from code.config import get_config

def test_decay_length_consistency():
    """
    Integration test for decay length consistency.
    """
    config = get_config()
    input_path = Path(config.DATA_DIR) / "processed" / "fit_results.json"
    
    assert input_path.exists(), "fit_results.json not found"
    
    with open(input_path, 'r') as f:
        data = json.load(f)
    
    assert len(data) > 0, "fit_results.json must not be empty"
    
    for item in data:
        assert item["R_squared"] >= 0.0, "R_squared must be valid"
        assert item["decay_length"] > 0, "decay_length must be positive"
