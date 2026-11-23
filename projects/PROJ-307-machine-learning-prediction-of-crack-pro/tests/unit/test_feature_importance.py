import pytest
import numpy as np
from code.analysis.feature_importance import aggregate_importance, get_top_features

def test_aggregate_importance_basic():
    """Test basic aggregation of importance scores."""
    models = [
        {"feature_a": 0.5, "feature_b": 0.3, "feature_c": 0.2},
        {"feature_a": 0.4, "feature_b": 0.4, "feature_c": 0.2},
        {"feature_a": 0.6, "feature_b": 0.2, "feature_c": 0.2}
    ]
    
    result = aggregate_importance(models)
    
    assert "feature_a" in result
    assert "feature_b" in result
    assert "feature_c" in result
    
    # Check mean calculation: feature_a should be (0.5+0.4+0.6)/3 = 0.5
    assert np.isclose(result["feature_a"], 0.5)
    assert np.isclose(result["feature_b"], 0.3)
    assert np.isclose(result["feature_c"], 0.2)

def test_aggregate_importance_empty():
    """Test aggregation with empty list."""
    result = aggregate_importance([])
    assert result == {}

def test_aggregate_importance_missing_features():
    """Test aggregation when features are missing in some models."""
    models = [
        {"feature_a": 0.5, "feature_b": 0.3},
        {"feature_a": 0.4, "feature_c": 0.6}  # feature_b missing, feature_c new
    ]
    
    result = aggregate_importance(models)
    
    # feature_a: (0.5 + 0.4) / 2 = 0.45
    assert np.isclose(result["feature_a"], 0.45)
    # feature_b: 0.3 / 2 = 0.15 (pandas mean treats missing as 0 in DataFrame mean)
    # Actually, pandas mean on a column with NaN treats NaN as 0 only if skipna=False.
    # Default skipna=True, so it divides by count of non-null.
    # Let's check the actual behavior: pd.DataFrame([{'a':1, 'b':2}, {'a':3}]).mean()
    # 'a': (1+3)/2 = 2.0, 'b': 2.0/1 = 2.0.
    # So missing values are ignored in the denominator for that specific column.
    assert "feature_b" in result
    assert "feature_c" in result

def test_get_top_features_basic():
    """Test basic top features extraction."""
    scores = {
        "feature_a": 0.9,
        "feature_b": 0.5,
        "feature_c": 0.2,
        "feature_d": 0.1
    }
    
    top = get_top_features(scores, n=2)
    
    assert len(top) == 2
    assert top[0] == ("feature_a", 0.9)
    assert top[1] == ("feature_b", 0.5)

def test_get_top_features_exclude():
    """Test top features extraction with exclusion."""
    scores = {
        "delta_K": 0.95,  # Should be excluded
        "feature_a": 0.8,
        "feature_b": 0.5,
        "feature_c": 0.2
    }
    
    top = get_top_features(scores, n=2, exclude_features=["delta_K"])
    
    assert len(top) == 2
    assert top[0] == ("feature_a", 0.8)
    assert top[1] == ("feature_b", 0.5)
    assert not any(f[0] == "delta_K" for f in top)

def test_get_top_features_all_excluded():
    """Test when all features are excluded."""
    scores = {"delta_K": 0.9, "other": 0.1}
    top = get_top_features(scores, n=2, exclude_features=["delta_K", "other"])
    assert top == []

def test_get_top_features_empty_scores():
    """Test with empty scores."""
    top = get_top_features({}, n=3)
    assert top == []

def test_get_top_features_less_than_n():
    """Test requesting more features than available."""
    scores = {"a": 1.0, "b": 0.5}
    top = get_top_features(scores, n=5)
    assert len(top) == 2
    assert top[0] == ("a", 1.0)
    assert top[1] == ("b", 0.5)
