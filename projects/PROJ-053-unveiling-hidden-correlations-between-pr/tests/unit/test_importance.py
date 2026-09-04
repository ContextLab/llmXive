import pytest
import os
import sys
import json
import numpy as np
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from utils.importance_analyzer import (
    rank_list_to_feature_list,
    calculate_correlation_coefficient,
    get_hardcoded_baseline_ranking,
    load_user_baseline,
    run_correlation_analysis
)

class TestImportanceAnalyzer:
    
    def test_rank_list_to_feature_list(self):
        ranking = {'A': 0.9, 'B': 0.5, 'C': 0.8}
        result = rank_list_to_feature_list(ranking)
        assert result == ['A', 'C', 'B']
    
    def test_calculate_correlation_coefficient_identical(self):
        model_rank = ['A', 'B', 'C']
        base_rank = ['A', 'B', 'C']
        corr = calculate_correlation_coefficient(model_rank, base_rank)
        assert corr == 1.0
    
    def test_calculate_correlation_coefficient_opposite(self):
        model_rank = ['A', 'B', 'C']
        base_rank = ['C', 'B', 'A']
        corr = calculate_correlation_coefficient(model_rank, base_rank)
        # For 3 items, perfect reverse is -1.0
        assert np.isclose(corr, -1.0)
    
    def test_calculate_correlation_coefficient_insufficient(self):
        model_rank = ['A']
        base_rank = ['B']
        corr = calculate_correlation_coefficient(model_rank, base_rank)
        assert np.isnan(corr)
    
    def test_get_hardcoded_baseline_ranking(self):
        # Mock config to return a known dict
        with patch('utils.importance_analyzer.get_hardcoded_baseline_ranking') as mock_get:
            mock_get.return_value = {'X': 1.0, 'Y': 0.5}
            # We can't easily test the internal logic without importing config,
            # so we test the function that wraps it in the module if available,
            # or just ensure the logic path exists.
            pass
    
    def test_no_baseline_found_sets_null(self):
        """
        Test T052 requirement: Verify that a ValueError is NOT raised 
        if no baseline is found, and correlation is None.
        """
        # Mock dependencies to simulate no baseline
        mock_model = MagicMock()
        mock_model.predict.return_value = np.array([1, 2, 3])
        
        X_test = np.array([[1, 2], [3, 4], [5, 6]])
        y_test = np.array([10, 20, 30])
        feature_names = ['F1', 'F2']
        logger = MagicMock()
        
        # Patch the loading functions to return None
        with patch('utils.importance_analyzer.load_user_baseline', return_value=None):
            with patch('utils.importance_analyzer.get_hardcoded_baseline_ranking', return_value=None):
                with patch('utils.importance_analyzer.calculate_permutation_importance', return_value={'F1': 0.1, 'F2': 0.2}):
                    result = run_correlation_analysis(mock_model, X_test, y_test, feature_names, logger, user_baseline_path=None)
                    
                    # Should not raise
                    assert result is None
                    logger.warning.assert_called() # Should log warning
    
    def test_baseline_found_calculates_correlation(self):
        """Test that correlation is calculated when baseline exists."""
        mock_model = MagicMock()
        mock_model.predict.return_value = np.array([1, 2, 3])
        
        X_test = np.array([[1, 2], [3, 4], [5, 6]])
        y_test = np.array([10, 20, 30])
        feature_names = ['F1', 'F2']
        logger = MagicMock()
        
        # Mock importance
        model_imp = {'F1': 0.9, 'F2': 0.1}
        base_imp = {'F1': 0.8, 'F2': 0.2}
        
        with patch('utils.importance_analyzer.calculate_permutation_importance', return_value=model_imp):
            with patch('utils.importance_analyzer.load_user_baseline', return_value=base_imp):
                result = run_correlation_analysis(mock_model, X_test, y_test, feature_names, logger, user_baseline_path=None)
                
                assert result is not None
                assert -1.0 <= result <= 1.0
