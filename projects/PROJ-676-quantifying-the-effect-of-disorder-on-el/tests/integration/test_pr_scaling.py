import json
import os
import pytest
from pathlib import Path
from code.config import get_config

def test_scaling_fits_existence():
    """
    Integration test for finite-size scaling workflow.
    Asserts existence of data/processed/scaling_fits.json.
    """
    config = get_config()
    output_path = Path(config.DATA_DIR) / "processed" / "scaling_fits.json"
    
    assert output_path.exists(), f"scaling_fits.json not found at {output_path}"
    
    with open(output_path, 'r') as f:
        data = json.load(f)
    
    assert isinstance(data, list), "scaling_fits.json must be a list"
    assert len(data) > 0, "scaling_fits.json must contain at least one result"
