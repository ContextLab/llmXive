import pytest
import numpy as np
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the functions to test
from utils.importance_analyzer import (
    load_user_baseline,
    get_hardcoded_baseline_ranking,
    rank_list_to_feature_list,
    calculate_correlation_coefficient,
    run_correlation_analysis
)

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_load_user_baseline_found(temp_dir):
    # Create a fake baseline file
    baseline_file = temp_dir / "data"
    baseline_file.mkdir()
    baseline_path = baseline_file / "baseline_importance.json"
    
    data = {"rankings": ["feature_a", "feature_b", "feature_c"]}
    with open(baseline_path, 'w') as f:
        json.dump(data, f)
    
    # Mock get_project_root to return temp_dir
    with patch('utils.importance_analyzer.get_project_root', return_value=temp_dir):
        # We need to mock the logger
        logger = MagicMock()
        result = load_user_baseline(logger)
        
        assert result == ["feature_a", "feature_b", "feature_c"]
        logger.info.assert_called()

def test_load_user_baseline_not_found(temp_dir):
    with patch('utils.importance_analyzer.get_project_root', return_value=temp_dir):
        logger = MagicMock()
        result = load_user_baseline(logger)
        
        assert result is None
        logger.info.assert_called()

def test_rank_list_to_feature_list():
    ranked_features = ["A", "B", "C"]
    result = rank_list_to_feature_list(ranked_features)
    assert result == [0, 1, 2]

def test_calculate_correlation_coefficient():
    ranks1 = [0, 1, 2]
    ranks2 = [0, 1, 2]
    corr = calculate_correlation_coefficient(ranks1, ranks2)
    assert corr == 1.0
    
    ranks3 = [2, 1, 0]
    corr2 = calculate_correlation_coefficient(ranks1, ranks3)
    assert corr2 == -1.0

def test_run_correlation_analysis_no_baseline(temp_dir):
    # Mock model and data
    model = MagicMock()
    X_test = np.array([[1, 2], [3, 4]])
    y_test = np.array([1, 2])
    feature_names = ["f1", "f2"]
    logger = MagicMock()
    
    # Mock all baseline loaders to return None
    with patch('utils.importance_analyzer.load_literature_baseline', return_value=None), \
         patch('utils.importance_analyzer.load_user_baseline', return_value=None), \
         patch('utils.importance_analyzer.get_hardcoded_baseline_ranking', return_value=None):
        
        result = run_correlation_analysis(model, X_test, y_test, feature_names, logger)
        
        assert result["baseline_found"] == False
        assert result["correlation_coefficient"] is None
        assert "No verified baseline found" in result["message"]
        logger.warning.assert_called()