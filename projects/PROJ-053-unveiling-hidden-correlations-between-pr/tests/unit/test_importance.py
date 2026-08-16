import os
import json
import tempfile
import pytest
import numpy as np
from unittest.mock import patch, MagicMock

# Import the function to test
from utils.importance_analyzer import (
    load_user_baseline, 
    rank_list_to_feature_list, 
    calculate_correlation_coefficient,
    run_correlation_analysis
)

@pytest.fixture
def temp_results_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

def test_load_user_baseline_missing_file(temp_results_dir):
    """Test that load_user_baseline raises FileNotFoundError when file is missing."""
    with pytest.raises(FileNotFoundError) as excinfo:
        load_user_baseline(temp_results_dir, MagicMock())
    assert "No verified baseline found" in str(excinfo.value)

def test_load_user_baseline_invalid_json(temp_results_dir):
    """Test that load_user_baseline raises ValueError for invalid JSON."""
    baseline_path = os.path.join(temp_results_dir, "baseline_importance.json")
    with open(baseline_path, 'w') as f:
        f.write("invalid json {")
    
    with pytest.raises(ValueError):
        load_user_baseline(temp_results_dir, MagicMock())

def test_load_user_baseline_missing_key(temp_results_dir):
    """Test that load_user_baseline raises ValueError if 'baseline_ranking' is missing."""
    baseline_path = os.path.join(temp_results_dir, "baseline_importance.json")
    with open(baseline_path, 'w') as f:
        json.dump({"other_key": ["a", "b"]}, f)
    
    with pytest.raises(ValueError):
        load_user_baseline(temp_results_dir, MagicMock())

def test_load_user_baseline_success(temp_results_dir):
    """Test successful loading of user baseline."""
    baseline_path = os.path.join(temp_results_dir, "baseline_importance.json")
    expected_ranking = ["feature_a", "feature_b", "feature_c"]
    with open(baseline_path, 'w') as f:
        json.dump({"baseline_ranking": expected_ranking}, f)
    
    result = load_user_baseline(temp_results_dir, MagicMock())
    assert result == expected_ranking

def test_rank_list_to_feature_list():
    """Test conversion of ranked names to integer ranks."""
    rank_list = ["feat1", "feat2", "feat3"]
    feature_names = ["feat3", "feat1", "feat2", "feat4"]
    
    # Expected: feat3(0), feat1(1), feat2(2), feat4(3) -> ranks: [0, 1, 2, 3]
    # Wait, rank_list is ordered: index 0 is most important.
    # feat3 is at index 2 in rank_list? No.
    # rank_list = ["feat1", "feat2", "feat3"] -> feat1 is rank 0, feat2 rank 1, feat3 rank 2.
    # feature_names = ["feat3", "feat1", "feat2", "feat4"]
    # feat3 -> rank 2
    # feat1 -> rank 0
    # feat2 -> rank 1
    # feat4 -> missing -> rank 3 (len(rank_list))
    
    expected = [2, 0, 1, 3]
    result = rank_list_to_feature_list(rank_list, feature_names)
    assert result == expected

def test_calculate_correlation_coefficient():
    """Test Spearman correlation calculation."""
    # Perfect correlation
    ranks1 = [0, 1, 2, 3]
    ranks2 = [0, 1, 2, 3]
    corr = calculate_correlation_coefficient(ranks1, ranks2, MagicMock())
    assert np.isclose(corr, 1.0)

    # Perfect negative correlation
    ranks1 = [0, 1, 2, 3]
    ranks2 = [3, 2, 1, 0]
    corr = calculate_correlation_coefficient(ranks1, ranks2, MagicMock())
    assert np.isclose(corr, -1.0)

    # No correlation (random)
    ranks1 = [0, 1, 2, 3]
    ranks2 = [1, 3, 0, 2]
    corr = calculate_correlation_coefficient(ranks1, ranks2, MagicMock())
    assert -1.0 < corr < 1.0

@patch('utils.importance_analyzer.load_user_baseline')
@patch('utils.importance_analyzer.calculate_permutation_importance')
@patch('utils.importance_analyzer.rank_list_to_feature_list')
@patch('utils.importance_analyzer.calculate_correlation_coefficient')
@patch('builtins.open', new_callable=MagicMock)
@patch('os.path.exists', return_value=True)
def test_run_correlation_analysis_success(
    mock_exists, mock_open, mock_corr, mock_ranks, mock_perm, mock_load_baseline
):
    """Test the full run_correlation_analysis flow."""
    mock_logger = MagicMock()
    mock_model = MagicMock()
    mock_X_test = np.array([[1, 2], [3, 4]])
    mock_y_test = np.array([1, 2])
    mock_feature_names = ["f1", "f2"]
    
    mock_load_baseline.return_value = ["f1", "f2"]
    mock_perm.return_value = (np.array([0.5, 0.1]), ["f1", "f2"])
    mock_ranks.side_effect = lambda x, y: [0, 1] if x == ["f1", "f2"] else [0, 1]
    mock_corr.return_value = 0.95
    
    # Mock file operations for metrics.json
    mock_file = MagicMock()
    mock_open.return_value.__enter__.return_value = mock_file
    
    results = run_correlation_analysis(
        mock_model, mock_X_test, mock_y_test, mock_feature_names, "/tmp/results", mock_logger
    )
    
    assert "permutation_importance" in results
    assert results["permutation_importance"]["correlation_with_baseline"] == 0.95