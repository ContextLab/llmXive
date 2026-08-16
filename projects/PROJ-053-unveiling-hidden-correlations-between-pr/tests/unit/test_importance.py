import os
import json
import pytest
import numpy as np
import pandas as pd
from unittest.mock import patch, MagicMock

from utils.importance_analyzer import (
    load_user_baseline, 
    load_literature_baseline, 
    get_hardcoded_baseline_ranking,
    rank_list_to_feature_list,
    calculate_correlation_coefficient,
    run_correlation_analysis
)
from config import get_hardcoded_baseline_ranking as cfg_get_baseline

def test_load_user_baseline_missing_file(tmp_path):
    """Test that load_user_baseline returns None when file is missing."""
    import logging
    logger = logging.getLogger("test")
    
    result = load_user_baseline(str(tmp_path / "nonexistent.json"), logger)
    assert result is None

def test_load_user_baseline_invalid_json(tmp_path):
    """Test that load_user_baseline returns None for invalid JSON."""
    bad_file = tmp_path / "bad.json"
    bad_file.write_text("not valid json")
    
    import logging
    logger = logging.getLogger("test")
    
    result = load_user_baseline(str(bad_file), logger)
    assert result is None

def test_load_user_baseline_missing_rankings_key(tmp_path):
    """Test that load_user_baseline returns None if 'rankings' key is missing."""
    good_file = tmp_path / "good.json"
    good_file.write_text(json.dumps({"other_key": {}}))
    
    import logging
    logger = logging.getLogger("test")
    
    result = load_user_baseline(str(good_file), logger)
    assert result is None

def test_load_user_baseline_success(tmp_path):
    """Test successful loading of user baseline."""
    data = {"rankings": {"laser_power": 1, "scan_speed": 2}}
    good_file = tmp_path / "good.json"
    good_file.write_text(json.dumps(data))
    
    import logging
    logger = logging.getLogger("test")
    
    result = load_user_baseline(str(good_file), logger)
    assert result == {"laser_power": 1, "scan_speed": 2}

def test_get_hardcoded_baseline_ranking():
    """Test that hardcoded baseline is retrieved correctly."""
    result = get_hardcoded_baseline_ranking()
    assert "rankings" in result
    assert "laser_power" in result["rankings"]

def test_rank_list_to_feature_list():
    """Test conversion of ranking dict to list."""
    rankings = {"A": 1, "B": 2}
    features = ["A", "B", "C"]
    
    result = rank_list_to_feature_list(rankings, features, logging.getLogger("test"))
    # C is missing, should get default rank 4 (len + 1)
    assert result == [1.0, 2.0, 4.0]

def test_calculate_correlation_coefficient():
    """Test Spearman correlation calculation."""
    model_ranks = [1.0, 2.0, 3.0]
    baseline_ranks = [1.0, 2.0, 3.0]
    
    corr = calculate_correlation_coefficient(model_ranks, baseline_ranks, logging.getLogger("test"))
    assert corr == 1.0

def test_run_correlation_analysis_no_baseline_raises():
    """Test that run_correlation_analysis raises FileNotFoundError if no baseline exists."""
    mock_model = MagicMock()
    X = np.array([[1, 2], [3, 4]])
    y = np.array([1, 2])
    features = ["A", "B"]
    
    with patch('utils.importance_analyzer.load_user_baseline', return_value=None):
        with patch('utils.importance_analyzer.get_hardcoded_baseline_ranking', return_value=None):
            with pytest.raises(FileNotFoundError, match="No baseline provided for SC-004"):
                run_correlation_analysis(
                    model=mock_model,
                    X_test=X,
                    y_test=y,
                    feature_names=features,
                    user_baseline_path=None,
                    output_path=None
                )
