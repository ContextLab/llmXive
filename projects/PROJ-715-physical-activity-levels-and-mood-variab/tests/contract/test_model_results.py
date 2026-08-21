import pytest
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))
from config import get_path

def test_model_results_schema():
    """
    Test that model_results.json exists and has basic structure.
    """
    path = get_path('data/processed/model_results.json')
    if not path.exists():
        pytest.skip("model_results.json not found. Run analysis first.")
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    assert 'model_type' in data
    assert 'fixed_effects' in data
    assert 'random_effects' in data
    assert 'model_fit' in data
    assert 'secondary_model' in data
    assert 'validation' in data
    assert 'sensitivity' in data
    assert 'diagnostics' in data