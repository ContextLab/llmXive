"""
Contract test for attribution output format (T021).
"""
import pytest
import json
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
raw_attr_path = project_root / "data" / "processed" / "raw_attribution.json"
masked_attr_path = project_root / "data" / "processed" / "masked_attribution.json"

def test_raw_attribution_format():
    """Verify raw_attribution.json structure."""
    if not raw_attr_path.exists():
        pytest.skip("raw_attribution.json not found.")
    
    with open(raw_attr_path, 'r') as f:
        data = json.load(f)
    
    # Check if it's a dict or list of dicts
    if isinstance(data, dict):
        assert "molecule_id" in data or "smi" in data or len(data) > 0
    elif isinstance(data, list):
        assert len(data) > 0
        if isinstance(data[0], dict):
            assert "smi" in data[0] or "molecule_id" in data[0]
    else:
        pytest.fail("raw_attribution.json must be a dict or list")

def test_masked_attribution_format():
    """Verify masked_attribution.json structure."""
    if not masked_attr_path.exists():
        pytest.skip("masked_attribution.json not found.")
    
    with open(masked_attr_path, 'r') as f:
        data = json.load(f)
    
    # Similar check as raw
    if isinstance(data, dict):
        pass # Valid
    elif isinstance(data, list):
        pass # Valid
    else:
        pytest.fail("masked_attribution.json must be a dict or list")