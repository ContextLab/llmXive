"""
Contract test for collinearity output in tests/test_collinearity.py (T007.1).
Assert redundancy_masks.json structure.
"""
import pytest
import json
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
redundancy_masks_path = project_root / "data" / "processed" / "redundancy_masks.json"

def test_redundancy_masks_structure():
    """Assert redundancy_masks.json structure: { "molecule_id": [mask_array] }."""
    if not redundancy_masks_path.exists():
        pytest.skip("redundancy_masks.json not found.")
    
    with open(redundancy_masks_path, 'r') as f:
        data = json.load(f)
    
    assert isinstance(data, dict), "redundancy_masks.json must be a dict"
    
    for key, value in data.items():
        assert isinstance(key, str), "Keys must be strings (molecule_id)"
        assert isinstance(value, list), "Values must be lists (mask_array)"
        if len(value) > 0:
            assert isinstance(value[0], bool), "Mask array elements must be booleans"
