import pytest
import numpy as np
import pandas as pd
import json
import tempfile
import os

# Import from the project's utils module
from utils.importance_analyzer import (
    load_literature_baseline,
    get_hardcoded_baseline_ranking,
    load_user_baseline,
    calculate_permutation_importance,
    rank_list_to_feature_list,
    calculate_correlation_coefficient
)

def test_get_hardcoded_baseline_ranking():
    """Test hardcoded baseline ranking retrieval."""
    ranking = get_hardcoded_baseline_ranking()
    
    assert ranking is not None
    assert isinstance(ranking, list)
    assert len(ranking) > 0
    
    # Verify structure
    for item in ranking:
        assert 'name' in item
        assert 'rank' in item
        assert isinstance(item['rank'], int)

def test_load_user_baseline():
    """Test loading user-provided baseline importance."""
    baseline_data = {
        "parameters": [
            {"name": "laser_power", "rank": 1},
            {"name": "scan_speed", "rank": 2},
            {"name": "layer_thickness", "rank": 3}
        ]
    }
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        json.dump(baseline_data, f)
        temp_path = f.name
    
    loaded = load_user_baseline(temp_path)
    
    assert loaded is not None
    assert len(loaded) == 3
    assert loaded[0]['name'] == 'laser_power'
    assert loaded[0]['rank'] == 1
    
    os.unlink(temp_path)

def test_load_user_baseline_missing_file():
    """Test loading user baseline with missing file."""
    result = load_user_baseline('/nonexistent/path/baseline.json')
    assert result is None

def test_load_literature_baseline():
    """Test loading literature baseline (mock)."""
    # This would normally fetch from crossref, but we test the fallback
    # Since we can't actually fetch, we verify the function exists and returns None
    # when fetch fails
    result = load_literature_baseline('invalid_doi')
    assert result is None

def test_calculate_permutation_importance():
    """Test permutation importance calculation."""
    # Create a simple mock model
    class MockModel:
        def predict(self, X):
            return np.sum(X, axis=1)
    
    # Create sample data
    np.random.seed(42)
    X = np.random.uniform(0, 1, (100, 3))
    y = np.sum(X, axis=1) + np.random.normal(0, 0.1, 100)
    
    model = MockModel()
    
    # Calculate permutation importance
    importance = calculate_permutation_importance(model, X, y, n_repeats=3)
    
    assert importance is not None
    assert isinstance(importance, dict)
    assert len(importance) == 3  # 3 features
    
    # All importances should be non-negative
    for feat, imp in importance.items():
        assert imp >= 0

def test_rank_list_to_feature_list():
    """Test conversion from rank list to feature list."""
    rank_list = [
        {"name": "laser_power", "rank": 1},
        {"name": "scan_speed", "rank": 2},
        {"name": "layer_thickness", "rank": 3}
    ]
    
    feature_list = rank_list_to_feature_list(rank_list)
    
    assert feature_list == ["laser_power", "scan_speed", "layer_thickness"]

def test_rank_list_to_feature_list_empty():
    """Test conversion with empty list."""
    rank_list = []
    feature_list = rank_list_to_feature_list(rank_list)
    assert feature_list == []

def test_calculate_correlation_coefficient():
    """Test correlation coefficient calculation."""
    list1 = [1, 2, 3, 4, 5]
    list2 = [1, 2, 3, 4, 5]
    
    corr = calculate_correlation_coefficient(list1, list2)
    
    # Perfect correlation
    assert corr == 1.0

def test_calculate_correlation_coefficient_inverse():
    """Test correlation with inverse relationship."""
    list1 = [1, 2, 3, 4, 5]
    list2 = [5, 4, 3, 2, 1]
    
    corr = calculate_correlation_coefficient(list1, list2)
    
    # Perfect negative correlation
    assert corr == -1.0

def test_calculate_correlation_coefficient_no_correlation():
    """Test correlation with no relationship."""
    list1 = [1, 2, 3, 4, 5]
    list2 = [3, 1, 4, 1, 5]
    
    corr = calculate_correlation_coefficient(list1, list2)
    
    # Should be between -1 and 1
    assert -1.0 <= corr <= 1.0

def test_calculate_correlation_coefficient_different_lengths():
    """Test correlation with different length lists."""
    list1 = [1, 2, 3, 4, 5]
    list2 = [1, 2, 3, 4]
    
    # Should handle different lengths gracefully
    corr = calculate_correlation_coefficient(list1, list2)
    
    # Should return a valid correlation or handle the error
    assert -1.0 <= corr <= 1.0 or corr is None
