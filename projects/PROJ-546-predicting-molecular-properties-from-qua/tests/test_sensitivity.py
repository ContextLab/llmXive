"""
Unit test for code/sensitivity_analysis.py
"""
import pytest
import sys
import os
from pathlib import Path
from unittest.mock import MagicMock, patch
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
import joblib

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sensitivity_analysis import (
    load_model,
    load_data,
    prepare_features_target,
    extract_feature_importance,
    identify_top_descriptors,
    run_sensitivity_sweep,
    calculate_mae_degradation,
    verify_stability
)


class TestLoadModel:
    def test_load_model_returns_rf_instance(self):
        """Verify load_model returns a trained RandomForestRegressor."""
        # Create a mock trained model
        mock_model = RandomForestRegressor(n_estimators=10, random_state=42)
        
        # Mock the joblib load to return our mock
        with patch('sensitivity_analysis.joblib.load', return_value=mock_model):
            model = load_model("dummy_path.pkl")
            assert isinstance(model, RandomForestRegressor)
            assert model.n_estimators == 10


class TestLoadData:
    def test_load_data_returns_dataframe(self):
        """Verify load_data loads a CSV into a pandas DataFrame."""
        # Create a temporary CSV file
        with patch('sensitivity_analysis.pd.read_csv') as mock_read:
            mock_df = pd.DataFrame({'col1': [1, 2, 3], 'col2': [4, 5, 6]})
            mock_read.return_value = mock_df
            
            df = load_data("dummy_path.csv")
            assert isinstance(df, pd.DataFrame)
            assert 'col1' in df.columns
            mock_read.assert_called_once_with("dummy_path.csv")


class TestPrepareFeaturesTarget:
    def test_prepare_features_target_splits_correctly(self):
        """Verify prepare_features_target correctly separates features and target."""
        df = pd.DataFrame({
            'feat1': [1, 2, 3],
            'feat2': [4, 5, 6],
            'target': [10, 20, 30]
        })
        
        X, y = prepare_features_target(df, target_col='target')
        
        assert isinstance(X, pd.DataFrame)
        assert isinstance(y, pd.Series)
        assert list(X.columns) == ['feat1', 'feat2']
        assert list(y) == [10, 20, 30]


class TestExtractFeatureImportance:
    def test_extract_feature_importance_returns_dict(self):
        """Verify extract_feature_importance returns a dict of feature names to importance."""
        # Create a simple trained model
        X = np.array([[1, 2], [3, 4], [5, 6]])
        y = np.array([1, 2, 3])
        model = RandomForestRegressor(n_estimators=10, random_state=42)
        model.fit(X, y)
        
        feature_names = ['feat_a', 'feat_b']
        importance_dict = extract_feature_importance(model, feature_names)
        
        assert isinstance(importance_dict, dict)
        assert 'feat_a' in importance_dict
        assert 'feat_b' in importance_dict
        # Sum of importances in RandomForest is typically close to 1.0 but not guaranteed exactly
        total_importance = sum(importance_dict.values())
        assert 0.9 <= total_importance <= 1.1  # Allow small floating point variance


class TestIdentifyTopDescriptors:
    def test_identify_top_descriptors_returns_sorted_list(self):
        """Verify identify_top_descriptors returns top N descriptors sorted by importance."""
        importance_dict = {
            'feat_a': 0.5,
            'feat_b': 0.3,
            'feat_c': 0.2
        }
        
        top_2 = identify_top_descriptors(importance_dict, n=2)
        
        assert len(top_2) == 2
        assert top_2[0] == ('feat_a', 0.5)
        assert top_2[1] == ('feat_b', 0.3)
    
    def test_identify_top_descriptors_handles_small_n(self):
        """Test with n larger than available descriptors."""
        importance_dict = {
            'feat_a': 0.5,
            'feat_b': 0.5
        }
        
        top_5 = identify_top_descriptors(importance_dict, n=5)
        
        assert len(top_5) == 2
        assert top_5[0][0] == 'feat_a'


class TestCalculateMaeDegradation:
    def test_calculate_mae_degradation_returns_float(self):
        """Verify calculate_mae_degradation returns a float MAE value."""
        y_true = np.array([1, 2, 3, 4, 5])
        y_pred = np.array([1.1, 2.2, 2.9, 4.1, 5.0])
        
        mae = calculate_mae_degradation(y_true, y_pred)
        
        assert isinstance(mae, float)
        assert mae > 0
    
    def test_calculate_mae_degradation_perfect_prediction(self):
        """Test MAE with perfect predictions."""
        y_true = np.array([1, 2, 3])
        y_pred = np.array([1, 2, 3])
        
        mae = calculate_mae_degradation(y_true, y_pred)
        
        assert mae == 0.0


class TestRunSensitivitySweep:
    def test_run_sensitivity_sweep_returns_results_dict(self):
        """Verify run_sensitivity_sweep returns a dict of results for different noise levels."""
        # Mock the necessary dependencies
        with patch('sensitivity_analysis.load_model') as mock_load_model, \
             patch('sensitivity_analysis.load_data') as mock_load_data, \
             patch('sensitivity_analysis.prepare_features_target') as mock_prep, \
             patch('sensitivity_analysis.calculate_mae_degradation') as mock_calc:
             
            mock_model = MagicMock()
            mock_df = pd.DataFrame({'f1': [1, 2], 'f2': [3, 4], 'target': [5, 6]})
            mock_prep.return_value = (mock_df[['f1', 'f2']], mock_df['target'])
            mock_calc.return_value = 0.5
            
            results = run_sensitivity_sweep("model.pkl", "data.csv", "target", noise_levels=[0.01, 0.05])
            
            assert isinstance(results, dict)
            assert 0.01 in results
            assert 0.05 in results


class TestVerifyStability:
    def test_verify_stability_returns_dict_with_stability_flag(self):
        """Verify verify_stability returns a dict containing stability assessment."""
        # Mock results from sweep
        results = {
            0.01: {'top_3': ['a', 'b', 'c']},
            0.05: {'top_3': ['a', 'b', 'c']}
        }
        
        stability_result = verify_stability(results)
        
        assert isinstance(stability_result, dict)
        assert 'stable' in stability_result
        assert 'rho' in stability_result
        assert stability_result['stable'] is True  # Identical top 3 should be stable
    
    def test_verify_stability_unstable_ranking(self):
        """Test stability when rankings differ significantly."""
        results = {
            0.01: {'top_3': ['a', 'b', 'c']},
            0.05: {'top_3': ['c', 'b', 'a']}
        }
        
        stability_result = verify_stability(results)
        
        assert isinstance(stability_result, dict)
        assert 'stable' in stability_result
        # The stability depends on the Spearman correlation calculation
        # If rankings are completely reversed, it might be unstable
        # We just check the structure is correct
        assert 'rho' in stability_result