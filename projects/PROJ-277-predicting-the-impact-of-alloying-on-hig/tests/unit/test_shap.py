"""
Unit tests for feature importance ranking logic (US3).

This module verifies that the feature importance ranking logic correctly:
1. Sorts features by mean absolute SHAP values
2. Identifies top-k features
3. Handles ties correctly
4. Validates input data structure
"""
import pytest
import numpy as np
import pandas as pd
from typing import List, Dict, Any
import sys
import os

# Add project root to path for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from code.viz.shap_plots import (
    rank_features_by_importance,
    get_top_k_features,
    validate_feature_importance_input
)


class TestFeatureImportanceRanking:
    """Unit tests for feature importance ranking logic."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_shap_values = {
            'Ni': np.array([0.1, 0.2, 0.3, 0.4, 0.5]),
            'Cr': np.array([0.3, 0.4, 0.5, 0.6, 0.7]),
            'Al': np.array([0.5, 0.6, 0.7, 0.8, 0.9]),
            'Fe': np.array([0.05, 0.1, 0.15, 0.2, 0.25]),
            'Ti': np.array([0.02, 0.03, 0.04, 0.05, 0.06]),
        }
        
        self.expected_ranking = [
            ('Al', 0.7),
            ('Cr', 0.5),
            ('Ni', 0.3),
            ('Fe', 0.15),
            ('Ti', 0.04),
        ]

    def test_rank_features_by_importance_correct_order(self):
        """Test that features are ranked by mean absolute SHAP values in descending order."""
        ranking = rank_features_by_importance(self.mock_shap_values)
        
        assert len(ranking) == len(self.mock_shap_values)
        assert ranking == self.expected_ranking

    def test_rank_features_by_importance_handles_empty_dict(self):
        """Test that an empty dictionary returns an empty list."""
        result = rank_features_by_importance({})
        assert result == []

    def test_rank_features_by_importance_single_feature(self):
        """Test ranking with a single feature."""
        single_feature = {'Al': np.array([0.5, 0.6, 0.7])}
        result = rank_features_by_importance(single_feature)
        
        assert len(result) == 1
        assert result[0][0] == 'Al'
        assert np.isclose(result[0][1], 0.6)

    def test_get_top_k_features_correct_count(self):
        """Test that get_top_k_features returns exactly k features."""
        ranking = rank_features_by_importance(self.mock_shap_values)
        
        for k in [1, 2, 3, 5]:
            top_k = get_top_k_features(ranking, k)
            assert len(top_k) == min(k, len(ranking))

    def test_get_top_k_features_correct_features(self):
        """Test that get_top_k_features returns the correct top features."""
        ranking = rank_features_by_importance(self.mock_shap_values)
        top_3 = get_top_k_features(ranking, 3)
        
        expected_top_3 = self.expected_ranking[:3]
        assert top_3 == expected_top_3

    def test_get_top_k_features_handles_k_greater_than_total(self):
        """Test that k > total features returns all features."""
        ranking = rank_features_by_importance(self.mock_shap_values)
        top_10 = get_top_k_features(ranking, 10)
        
        assert len(top_10) == len(ranking)
        assert top_10 == ranking

    def test_validate_feature_importance_input_valid(self):
        """Test validation with valid input."""
        is_valid, error_msg = validate_feature_importance_input(self.mock_shap_values)
        
        assert is_valid is True
        assert error_msg is None

    def test_validate_feature_importance_input_empty(self):
        """Test validation with empty input."""
        is_valid, error_msg = validate_feature_importance_input({})
        
        assert is_valid is False
        assert "empty" in error_msg.lower()

    def test_validate_feature_importance_input_non_array_values(self):
        """Test validation with non-array values."""
        invalid_input = {'Al': [0.5, 0.6, 0.7], 'Cr': 'not_an_array'}
        is_valid, error_msg = validate_feature_importance_input(invalid_input)
        
        assert is_valid is False
        assert "numpy array" in error_msg.lower()

    def test_validate_feature_importance_input_mismatched_lengths(self):
        """Test validation with mismatched array lengths."""
        invalid_input = {
            'Al': np.array([0.5, 0.6, 0.7]),
            'Cr': np.array([0.3, 0.4])
        }
        is_valid, error_msg = validate_feature_importance_input(invalid_input)
        
        assert is_valid is False
        assert "length" in error_msg.lower()

    def test_ranking_consistency_across_calls(self):
        """Test that ranking is deterministic across multiple calls."""
        ranking1 = rank_features_by_importance(self.mock_shap_values)
        ranking2 = rank_features_by_importance(self.mock_shap_values)
        
        assert ranking1 == ranking2

    def test_tie_handling(self):
        """Test that ties in SHAP values are handled consistently."""
        tied_input = {
            'A': np.array([0.5, 0.5, 0.5]),
            'B': np.array([0.5, 0.5, 0.5]),
            'C': np.array([0.3, 0.3, 0.3]),
        }
        ranking = rank_features_by_importance(tied_input)
        
        # A and B should both have mean 0.5, C should have 0.3
        assert ranking[0][0] in ['A', 'B']
        assert ranking[1][0] in ['A', 'B']
        assert ranking[0][0] != ranking[1][0]
        assert ranking[2][0] == 'C'
        assert np.isclose(ranking[0][1], 0.5)
        assert np.isclose(ranking[1][1], 0.5)
        assert np.isclose(ranking[2][1], 0.3)

    def test_negative_shap_values(self):
        """Test that negative SHAP values are handled correctly (absolute value)."""
        negative_input = {
            'Al': np.array([-0.5, -0.6, -0.7]),
            'Cr': np.array([0.3, 0.4, 0.5]),
        }
        ranking = rank_features_by_importance(negative_input)
        
        # Al should be ranked higher due to larger absolute values
        assert ranking[0][0] == 'Al'
        assert np.isclose(ranking[0][1], 0.6)  # mean of absolute values
        assert ranking[1][0] == 'Cr'
        assert np.isclose(ranking[1][1], 0.4)

    def test_zero_shap_values(self):
        """Test handling of zero SHAP values."""
        zero_input = {
            'Al': np.array([0.0, 0.0, 0.0]),
            'Cr': np.array([0.1, 0.2, 0.3]),
        }
        ranking = rank_features_by_importance(zero_input)
        
        assert ranking[0][0] == 'Cr'
        assert ranking[1][0] == 'Al'
        assert np.isclose(ranking[1][1], 0.0)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])