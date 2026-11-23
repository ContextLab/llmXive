import os
import json
import pytest
import numpy as np
from unittest.mock import patch, MagicMock

# Adjust import based on project structure
from code.utils.importance_analyzer import (
    get_hardcoded_baseline_ranking,
    load_user_baseline,
    rank_list_to_feature_list,
    calculate_correlation_coefficient,
    run_correlation_analysis
)

def test_get_hardcoded_baseline_ranking():
    ranking = get_hardcoded_baseline_ranking()
    assert 'laser_power' in ranking
    assert ranking['laser_power'] == 1
    assert ranking['scan_speed'] == 2
    assert ranking['layer_thickness'] == 3

def test_rank_list_to_feature_list():
    rankings = {'A': 1, 'B': 2, 'C': 3}
    features = ['C', 'A', 'B']
    ranks = rank_list_to_feature_list(rankings, features)
    assert ranks == [3, 1, 2]

def test_rank_list_to_feature_list_missing():
    rankings = {'A': 1}
    features = ['A', 'B']
    ranks = rank_list_to_feature_list(rankings, features)
    # B is missing, should be len(features) + 1 = 3
    assert ranks == [1, 3]

def test_calculate_correlation_coefficient():
    # Perfect correlation
    m = [1, 2, 3]
    b = [1, 2, 3]
    corr, p = calculate_correlation_coefficient(m, b)
    assert np.isclose(corr, 1.0)
    
    # Inverse correlation
    m = [1, 2, 3]
    b = [3, 2, 1]
    corr, p = calculate_correlation_coefficient(m, b)
    assert np.isclose(corr, -1.0)

@patch('code.utils.importance_analyzer.load_user_baseline')
@patch('code.utils.importance_analyzer.load_literature_baseline')
@patch('code.utils.importance_analyzer.calculate_permutation_importance')
@patch('code.utils.importance_analyzer.logger')
def test_run_correlation_analysis_success(mock_logger, mock_perm, mock_lit, mock_user):
    # Mock data
    mock_model = MagicMock()
    X = np.random.rand(10, 3)
    y = np.random.rand(10)
    features = ['A', 'B', 'C']
    
    # Mock importance
    mock_perm.return_value = {'A': 0.5, 'B': 0.2, 'C': 0.1}
    
    # Mock user baseline missing, literature present
    mock_user.return_value = None
    mock_lit.return_value = {'A': 1, 'B': 2, 'C': 3}
    
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        temp_path = f.name
    
    try:
        run_correlation_analysis(mock_model, X, y, features, temp_path)
        
        # Check file exists and content
        assert os.path.exists(temp_path)
        with open(temp_path, 'r') as f:
            data = json.load(f)
        
        assert data['status'] == 'success'
        assert data['baseline_source'] == 'literature'
        assert 'correlation_coefficient' in data
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@patch('code.utils.importance_analyzer.load_user_baseline')
@patch('code.utils.importance_analyzer.load_literature_baseline')
@patch('code.utils.importance_analyzer.logger')
def test_run_correlation_analysis_no_baseline(mock_logger, mock_lit, mock_user):
    mock_model = MagicMock()
    X = np.random.rand(10, 3)
    y = np.random.rand(10)
    features = ['A', 'B', 'C']
    
    mock_user.return_value = None
    mock_lit.return_value = None
    
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        temp_path = f.name
    
    try:
        run_correlation_analysis(mock_model, X, y, features, temp_path)
        
        with open(temp_path, 'r') as f:
            data = json.load(f)
        
        assert data['status'] == 'skipped'
        assert "No baseline available" in data['reason']
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
