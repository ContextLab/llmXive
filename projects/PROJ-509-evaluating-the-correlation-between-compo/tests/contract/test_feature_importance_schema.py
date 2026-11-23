import pytest
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from code.config import load_paths

def test_permutation_importance_schema():
    """Test that permutation_importance.json matches expected schema."""
    paths = load_paths()
    file_path = os.path.join(paths['evaluation_dir'], 'permutation_importance.json')
    
    if not os.path.exists(file_path):
        pytest.skip(f"File {file_path} does not exist yet. Run code/importance.py first.")
    
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    # Check required keys
    required_keys = ["correlation_coefficient", "p_value", "threshold_met", "permutation_importance_scores"]
    for key in required_keys:
        assert key in data, f"Missing required key: {key}"
    
    # Check types
    assert isinstance(data['correlation_coefficient'], float)
    assert isinstance(data['p_value'], float)
    assert isinstance(data['threshold_met'], bool)
    assert isinstance(data['permutation_importance_scores'], dict)
    
    # Check correlation bounds
    assert -1.0 <= data['correlation_coefficient'] <= 1.0

def test_feature_ranking_schema():
    """Test that feature_ranking.json matches expected schema."""
    paths = load_paths()
    file_path = os.path.join(paths['evaluation_dir'], 'feature_ranking.json')
    
    if not os.path.exists(file_path):
        pytest.skip(f"File {file_path} does not exist yet. Run code/importance.py first.")
    
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    assert "top_features" in data
    assert "method" in data
    
    features = data['top_features']
    assert isinstance(features, list)
    assert len(features) > 0
    
    for item in features:
        assert "rank" in item
        assert "feature" in item
        assert "importance" in item
        assert isinstance(item['rank'], int)
        assert isinstance(item['feature'], str)
        assert isinstance(item['importance'], (int, float))

def test_vif_scores_schema():
    """Test that vif_scores.json matches expected schema."""
    paths = load_paths()
    file_path = os.path.join(paths['evaluation_dir'], 'vif_scores.json')
    
    if not os.path.exists(file_path):
        pytest.skip(f"File {file_path} does not exist yet. Run code/importance.py first.")
    
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    assert "vif_scores" in data
    assert "threshold" in data
    assert "high_collinearity_features" in data
    
    assert isinstance(data['vif_scores'], dict)
    assert isinstance(data['threshold'], float)
    assert isinstance(data['high_collinearity_features'], list)