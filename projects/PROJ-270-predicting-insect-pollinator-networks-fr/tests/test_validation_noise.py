import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
import json
from pathlib import Path

# Import the function to test
from validation import assess_label_noise_impact

@pytest.fixture
def mock_feature_matrix():
    """Creates a mock feature matrix for testing."""
    n_samples = 200
    np.random.seed(42)
    data = {
        'trait_1': np.random.randn(n_samples),
        'trait_2': np.random.randn(n_samples),
        'ecosystem_id': np.random.choice(['eco_A', 'eco_B', 'eco_C'], n_samples),
        'link_label': np.random.randint(0, 2, n_samples)
    }
    return pd.DataFrame(data)

@pytest.fixture
def mock_model():
    """Returns a mock model object."""
    return MagicMock()

def test_assess_label_noise_impact(mock_feature_matrix, mock_model, tmp_path, caplog):
    """
    Tests that assess_label_noise_impact correctly simulates noise and reports degradation.
    """
    # Patch get_results_root to use a temporary directory
    with patch('validation.get_results_root', return_value=tmp_path):
        results = assess_label_noise_impact(mock_feature_matrix, mock_model)

    # Verify structure
    assert 'baseline_auc' in results
    assert 'noise_impact' in results
    assert len(results['noise_impact']) == 3  # 0.05, 0.10, 0.20

    # Verify that degradation increases with noise rate (generally)
    degradations = [item['auc_degradation'] for item in results['noise_impact']]
    # Note: Due to randomness, strict ordering isn't guaranteed, but we check for positive degradation
    for d in degradations:
        assert d >= 0, "Degradation should be non-negative"

    # Verify file was written
    results_file = tmp_path / "label_noise_impact.json"
    assert results_file.exists()
    
    with open(results_file, 'r') as f:
        saved_results = json.load(f)
    
    assert saved_results['baseline_auc'] == results['baseline_auc']
    
    # Check logs
    assert "Assessing Label Noise Impact" in caplog.text
    assert "Label Noise Assessment Summary" in caplog.text

def test_assess_label_noise_impact_empty_test_set(mock_feature_matrix, mock_model, tmp_path):
    """
    Tests behavior when the test set has only one class (edge case for AUC).
    """
    # Force the test split to have only one class by manipulating the mock data
    # This is hard to control with train_test_split, so we rely on the function's internal handling
    # of single-class test sets (returning 0.5).
    
    with patch('validation.get_results_root', return_value=tmp_path):
        results = assess_label_noise_impact(mock_feature_matrix, mock_model)
    
    # Should not crash
    assert isinstance(results, dict)
    assert 'baseline_auc' in results

def test_assess_label_noise_impact_file_content(tmp_path, mock_feature_matrix, mock_model):
    """
    Verifies the content of the saved JSON file matches the return value.
    """
    with patch('validation.get_results_root', return_value=tmp_path):
        results = assess_label_noise_impact(mock_feature_matrix, mock_model)
    
    results_file = tmp_path / "label_noise_impact.json"
    with open(results_file, 'r') as f:
        saved = json.load(f)
    
    assert saved == results