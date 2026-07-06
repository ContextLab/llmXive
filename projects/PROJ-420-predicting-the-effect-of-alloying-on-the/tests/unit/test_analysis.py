"""
Unit tests for analysis logic in code/analysis.py.

This module tests the feature importance extraction, permutation importance,
VIF calculation, and ranking comparison functions.
"""
import pytest
import numpy as np
import pandas as pd
import pickle
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis import (
    load_trained_model,
    extract_feature_importance,
    save_importance_results,
    run_permutation_importance,
    calculate_vif,
    save_vif_results,
    rank_and_compare_importance,
    run_importance_analysis
)
from config import get_config


class TestLoadTrainedModel:
    """Tests for load_trained_model function."""

    def test_load_existing_model(self, tmp_path):
        """Test loading a valid trained model."""
        # Create a mock model and save it
        mock_model = Mock()
        mock_model.feature_importances_ = np.array([0.1, 0.2, 0.3, 0.4])
        
        model_path = tmp_path / "rf_model.pkl"
        with open(model_path, 'wb') as f:
            pickle.dump(mock_model, f)
        
        # Test loading
        loaded_model = load_trained_model(model_path)
        assert loaded_model is not None
        np.testing.assert_array_equal(
            loaded_model.feature_importances_, 
            mock_model.feature_importances_
        )

    def test_load_missing_model(self, tmp_path):
        """Test loading a non-existent model raises error."""
        model_path = tmp_path / "non_existent.pkl"
        
        with pytest.raises(FileNotFoundError):
            load_trained_model(model_path)


class TestExtractFeatureImportance:
    """Tests for extract_feature_importance function."""

    def test_extract_importance_from_rf(self):
        """Test extracting importance from Random Forest."""
        mock_model = Mock()
        mock_model.feature_importances_ = np.array([0.1, 0.2, 0.3, 0.4])
        
        feature_names = ['ilr_1', 'ilr_2', 'ilr_3', 'ilr_4']
        
        importance_dict = extract_feature_importance(mock_model, feature_names)
        
        assert isinstance(importance_dict, dict)
        assert len(importance_dict) == 4
        assert 'ilr_1' in importance_dict
        assert importance_dict['ilr_4'] == 0.4

    def test_extract_with_empty_importances(self):
        """Test handling of empty feature importances."""
        mock_model = Mock()
        mock_model.feature_importances_ = np.array([])
        
        with pytest.raises(ValueError):
            extract_feature_importance(mock_model, [])


class TestSaveImportanceResults:
    """Tests for save_importance_results function."""

    def test_save_importance_to_file(self, tmp_path):
        """Test saving importance results to JSON."""
        importance_data = {
            'ilr_1': 0.25,
            'ilr_2': 0.35,
            'ilr_3': 0.20,
            'ilr_4': 0.20
        }
        
        output_path = tmp_path / "importance_results.json"
        save_importance_results(importance_data, output_path)
        
        assert output_path.exists()
        
        # Verify content
        with open(output_path, 'r') as f:
            import json
            loaded = json.load(f)
        
        assert loaded == importance_data


class TestRunPermutationImportance:
    """Tests for run_permutation_importance function."""

    @patch('sklearn.inspection.permutation_importance')
    def test_permutation_importance_calculation(self, mock_perm_importance, tmp_path):
        """Test running permutation importance."""
        # Mock the sklearn function
        mock_result = Mock()
        mock_result.importances_mean = np.array([0.1, 0.2, 0.15, 0.05])
        mock_perm_importance.return_value = mock_result
        
        mock_model = Mock()
        mock_model.predict = Mock(return_value=np.array([0.1, 0.2, 0.3]))
        
        X_test = pd.DataFrame({
            'ilr_1': [0.1, 0.2],
            'ilr_2': [0.3, 0.4],
            'ilr_3': [0.5, 0.6],
            'ilr_4': [0.7, 0.8]
        })
        y_test = np.array([0.1, 0.2])
        
        feature_names = ['ilr_1', 'ilr_2', 'ilr_3', 'ilr_4']
        
        importance_dict = run_permutation_importance(
            mock_model, X_test, y_test, feature_names
        )
        
        assert isinstance(importance_dict, dict)
        assert len(importance_dict) == 4
        assert 'ilr_2' in importance_dict
        
        # Verify sklearn was called
        mock_perm_importance.assert_called_once()


class TestCalculateVIF:
    """Tests for calculate_vif function."""

    def test_vif_calculation_with_collinearity(self):
        """Test VIF calculation with known collinearity."""
        # Create data with perfect collinearity (X2 = 2*X1)
        data = pd.DataFrame({
            'Cu': [1.0, 2.0, 3.0, 4.0],
            'Mg': [2.0, 4.0, 6.0, 8.0],  # Perfectly correlated with Cu
            'Si': [1.0, 1.0, 1.0, 1.0],
            'Zn': [0.5, 0.5, 0.5, 0.5],
            'Mn': [0.1, 0.2, 0.3, 0.4]
        })
        
        vif_results = calculate_vif(data)
        
        assert isinstance(vif_results, dict)
        assert 'Cu' in vif_results
        assert 'Mg' in vif_results
        
        # Mg should have very high VIF due to collinearity
        assert vif_results['Mg'] > 10  # Threshold for high collinearity

    def test_vif_with_independent_variables(self):
        """Test VIF with independent variables."""
        np.random.seed(42)
        data = pd.DataFrame({
            'Cu': np.random.rand(100),
            'Mg': np.random.rand(100),
            'Si': np.random.rand(100),
            'Zn': np.random.rand(100),
            'Mn': np.random.rand(100)
        })
        
        vif_results = calculate_vif(data)
        
        # All VIFs should be relatively low (< 5)
        for feature, vif in vif_results.items():
            assert vif < 5, f"Unexpected high VIF for {feature}: {vif}"

    def test_vif_with_constant_column(self):
        """Test VIF handling of constant columns."""
        data = pd.DataFrame({
            'Cu': [1.0, 2.0, 3.0],
            'Mg': [5.0, 5.0, 5.0],  # Constant
            'Si': [1.0, 2.0, 3.0]
        })
        
        # Should not crash, but may return inf or high values
        vif_results = calculate_vif(data)
        assert isinstance(vif_results, dict)


class TestSaveVifResults:
    """Tests for save_vif_results function."""

    def test_save_vif_to_file(self, tmp_path):
        """Test saving VIF results to JSON."""
        vif_data = {
            'Cu': 2.5,
            'Mg': 3.1,
            'Si': 1.8,
            'Zn': 2.2,
            'Mn': 1.5
        }
        
        output_path = tmp_path / "vif_results.json"
        save_vif_results(vif_data, output_path)
        
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            import json
            loaded = json.load(f)
        
        assert loaded == vif_data


class TestRankAndCompareImportance:
    """Tests for rank_and_compare_importance function."""

    def test_ranking_importance(self):
        """Test ranking feature importance."""
        importance_data = {
            'Cu': 0.35,
            'Mg': 0.25,
            'Si': 0.15,
            'Zn': 0.15,
            'Mn': 0.10
        }
        
        ranked, comparison = rank_and_compare_importance(importance_data)
        
        assert isinstance(ranked, list)
        assert len(ranked) == 5
        
        # Check ranking order (highest to lowest)
        assert ranked[0]['feature'] == 'Cu'
        assert ranked[0]['importance'] == 0.35
        assert ranked[-1]['feature'] == 'Mn'
        assert ranked[-1]['importance'] == 0.10
        
        assert isinstance(comparison, dict)
        assert 'top_feature' in comparison
        assert comparison['top_feature'] == 'Cu'

    def test_ranking_with_ties(self):
        """Test ranking with tied importance values."""
        importance_data = {
            'Cu': 0.25,
            'Mg': 0.25,
            'Si': 0.25,
            'Zn': 0.15,
            'Mn': 0.10
        }
        
        ranked, comparison = rank_and_compare_importance(importance_data)
        
        # Should handle ties gracefully
        assert len(ranked) == 5
        assert comparison['top_feature'] in ['Cu', 'Mg', 'Si']


class TestRunImportanceAnalysis:
    """Tests for run_importance_analysis function."""

    @patch('analysis.load_trained_model')
    @patch('analysis.extract_feature_importance')
    @patch('analysis.run_permutation_importance')
    @patch('analysis.calculate_vif')
    @patch('analysis.rank_and_compare_importance')
    def test_full_analysis_pipeline(
        self, 
        mock_rank, 
        mock_vif, 
        mock_perm, 
        mock_extract, 
        mock_load,
        tmp_path
    ):
        """Test running the complete importance analysis."""
        # Setup mocks
        mock_model = Mock()
        mock_load.return_value = mock_model
        mock_extract.return_value = {'ilr_1': 0.25, 'ilr_2': 0.75}
        mock_perm.return_value = {'ilr_1': 0.1, 'ilr_2': 0.3}
        mock_vif.return_value = {'Cu': 2.0, 'Mg': 3.0}
        mock_rank.return_value = (
            [{'feature': 'ilr_2', 'importance': 0.75}], 
            {'top_feature': 'ilr_2'}
        )
        
        # Create mock data
        X_test = pd.DataFrame({
            'ilr_1': [0.1, 0.2],
            'ilr_2': [0.3, 0.4]
        })
        y_test = np.array([0.1, 0.2])
        
        feature_names = ['ilr_1', 'ilr_2']
        raw_feature_names = ['Cu', 'Mg']
        
        results = run_importance_analysis(
            model_path=tmp_path / "model.pkl",
            X_test=X_test,
            y_test=y_test,
            feature_names=feature_names,
            raw_feature_names=raw_feature_names,
            output_dir=tmp_path
        )
        
        assert isinstance(results, dict)
        assert 'feature_importance' in results
        assert 'permutation_importance' in results
        assert 'vif_results' in results
        assert 'ranking' in results

        # Verify all mocks were called
        mock_load.assert_called_once()
        mock_extract.assert_called_once()
        mock_perm.assert_called_once()
        mock_vif.assert_called_once()
        mock_rank.assert_called_once()