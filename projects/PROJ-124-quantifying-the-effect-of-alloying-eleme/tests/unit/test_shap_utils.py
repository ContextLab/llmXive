"""
Unit tests for SHAP utility functions.
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import tempfile
import os

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.shap_utils import (
    ensure_shap_available,
    get_feature_importance_from_shap
)

def test_ensure_shap_available():
    """Test that SHAP availability check works."""
    # This might be True or False depending on environment
    result = ensure_shap_available()
    assert isinstance(result, bool)

def test_get_feature_importance_from_shap():
    """Test extraction of feature importance from SHAP results."""
    # Mock SHAP results
    mock_results = {
        "sorted_features": ["Feature_A", "Feature_B", "Feature_C"],
        "sorted_importance": [0.5, 0.3, 0.2],
        "mean_abs_shap": [0.5, 0.3, 0.2],
        "feature_names": ["Feature_A", "Feature_B", "Feature_C"]
    }
    
    top_features = get_feature_importance_from_shap(mock_results, top_n=2)
    
    assert len(top_features) == 2
    assert top_features[0]["feature"] == "Feature_A"
    assert top_features[0]["importance"] == 0.5
    assert top_features[1]["feature"] == "Feature_B"
    assert top_features[1]["importance"] == 0.3

def test_get_feature_importance_top_n():
    """Test that top_n parameter limits the output correctly."""
    mock_results = {
        "sorted_features": ["F1", "F2", "F3", "F4", "F5"],
        "sorted_importance": [0.1, 0.2, 0.3, 0.4, 0.5],
        "feature_names": ["F1", "F2", "F3", "F4", "F5"]
    }
    
    result = get_feature_importance_from_shap(mock_results, top_n=3)
    assert len(result) == 3
    
    result_all = get_feature_importance_from_shap(mock_results, top_n=10)
    assert len(result_all) == 5