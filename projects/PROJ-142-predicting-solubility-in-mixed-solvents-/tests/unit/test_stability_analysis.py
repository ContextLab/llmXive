"""
Unit tests for T034 stability analysis functionality.
"""
import json
import tempfile
from pathlib import Path
import numpy as np
import pytest

from code import stability_analysis
from utils.errors import CustomDataError


def test_compute_feature_rankings():
    """Test that feature rankings are computed correctly."""
    # Create a simple SHAP matrix where feature 0 has highest mean abs value
    shap_values = np.array([
        [10.0, 1.0, 0.5],
        [12.0, 0.8, 0.3],
        [8.0, 1.2, 0.6]
    ])
    
    ranks = stability_analysis.compute_feature_rankings(shap_values)
    
    # Feature 0 should be rank 0 (most important)
    assert ranks[0] == 0, f"Expected feature 0 to be rank 0, got {ranks[0]}"
    # Feature 1 should be rank 1
    assert ranks[1] == 1, f"Expected feature 1 to be rank 1, got {ranks[1]}"
    # Feature 2 should be rank 2 (least important)
    assert ranks[2] == 2, f"Expected feature 2 to be rank 2, got {ranks[2]}"


def test_calculate_spearman_stability():
    """Test Spearman stability calculation with known inputs."""
    # Create two folds with identical rankings (perfect correlation)
    shap_by_fold = {
        0: np.array([[10, 5, 1], [10, 5, 1]]),
        1: np.array([[10, 5, 1], [10, 5, 1]])
    }
    feature_names = ['f1', 'f2', 'f3']
    
    results = stability_analysis.calculate_spearman_stability(shap_by_fold, feature_names)
    
    assert results['stability_pass'] is True
    assert results['min_correlation'] == 1.0
    assert results['mean_correlation'] == 1.0


def test_calculate_spearman_stability_low_stability():
    """Test Spearman stability calculation with poor correlation."""
    # Create folds with reversed rankings (negative correlation)
    shap_by_fold = {
        0: np.array([[10, 5, 1], [10, 5, 1]]),  # f1 > f2 > f3
        1: np.array([[1, 5, 10], [1, 5, 10]])   # f3 > f2 > f1
    }
    feature_names = ['f1', 'f2', 'f3']
    
    results = stability_analysis.calculate_spearman_stability(shap_by_fold, feature_names)
    
    # Should fail the stability threshold
    assert results['stability_pass'] is False
    assert results['min_correlation'] < 0.5


def test_append_to_shap_ranking():
    """Test appending results to shap_ranking.json."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "shap_ranking.json"
        
        results = {
            "mean_correlation": 0.85,
            "stability_pass": True
        }
        
        stability_analysis.append_to_shap_ranking(results, output_path)
        
        # Verify file was created and contains results
        assert output_path.exists()
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert "stability_analysis" in data
        assert data["stability_analysis"]["mean_correlation"] == 0.85


def test_load_shap_values_from_cv_missing_file():
    """Test error handling when CV results file is missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        non_existent_path = Path(tmpdir) / "non_existent.json"
        
        with pytest.raises(CustomDataError):
            stability_analysis.load_shap_values_from_cv(non_existent_path)


def test_load_shap_values_from_cv_invalid_structure():
    """Test error handling for invalid JSON structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        invalid_path = Path(tmpdir) / "invalid.json"
        with open(invalid_path, 'w') as f:
            json.dump({"wrong_structure": True}, f)
        
        with pytest.raises(CustomDataError):
            stability_analysis.load_shap_values_from_cv(invalid_path)