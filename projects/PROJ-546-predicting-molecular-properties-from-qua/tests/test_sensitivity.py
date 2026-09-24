"""
Unit tests for code/sensitivity_analysis.py (User Story 3).

These tests verify the sensitivity analysis logic, including:
1. Feature importance extraction and sorting.
2. Cumulative importance calculation.
3. Top descriptor identification.
4. Sensitivity sweep (noise injection and re-training).
5. Rank correlation and stability verification.

Note: These tests use mock data and mocks for model training to ensure
they run quickly and independently of the full pipeline execution.
"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import json
import tempfile
from pathlib import Path

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from sensitivity_analysis import (
    setup_logger,
    load_model,
    load_data,
    prepare_features_target,
    extract_feature_importance,
    identify_top_descriptors,
    run_sensitivity_sweep,
    calculate_mae_degradation,
    verify_stability,
    generate_summary_report
)


class TestSensitivityAnalysis:
    """Unit tests for sensitivity analysis functions."""

    @pytest.fixture
    def mock_model(self):
        """Create a mock Random Forest model with feature_importances_."""
        model = Mock()
        # Simulate feature importances that sum to 1.0
        model.feature_importances_ = np.array([0.5, 0.3, 0.15, 0.05])
        return model

    @pytest.fixture
    def mock_data(self):
        """Create mock feature and target data."""
        X = pd.DataFrame({
            'feature_1': [1.0, 2.0, 3.0, 4.0],
            'feature_2': [2.0, 3.0, 4.0, 5.0],
            'feature_3': [3.0, 4.0, 5.0, 6.0],
            'feature_4': [4.0, 5.0, 6.0, 7.0]
        })
        y = pd.Series([10.0, 20.0, 30.0, 40.0])
        return X, y

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test outputs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    def test_extract_feature_importance(self, mock_model):
        """Test that feature importances are extracted and sorted correctly."""
        importances = extract_feature_importance(mock_model)
        
        assert isinstance(importances, pd.DataFrame)
        assert 'descriptor' in importances.columns
        assert 'importance' in importances.columns
        assert 'cumulative_importance' in importances.columns
        
        # Check sorting (descending)
        assert importances['importance'].is_monotonic_decreasing
        
        # Check values match mock model
        expected_importances = [0.5, 0.3, 0.15, 0.05]
        assert np.allclose(importances['importance'].values, expected_importances)
        
        # Check cumulative sum
        expected_cumulative = [0.5, 0.8, 0.95, 1.0]
        assert np.allclose(importances['cumulative_importance'].values, expected_cumulative)

    def test_identify_top_descriptors(self):
        """Test top descriptor identification with different cutoffs."""
        # Create a mock DataFrame with importance data
        importances = pd.DataFrame({
            'rank': [1, 2, 3, 4],
            'descriptor': ['f1', 'f2', 'f3', 'f4'],
            'importance': [0.5, 0.3, 0.15, 0.05],
            'cumulative_importance': [0.5, 0.8, 0.95, 1.0]
        })
        
        # Test with cutoff 0.8 (should include f1 and f2)
        top_2 = identify_top_descriptors(importances, cutoff=0.8)
        assert len(top_2) == 2
        assert top_2['descriptor'].tolist() == ['f1', 'f2']
        
        # Test with cutoff 0.95 (should include f1, f2, f3)
        top_3 = identify_top_descriptors(importances, cutoff=0.95)
        assert len(top_3) == 3
        assert top_3['descriptor'].tolist() == ['f1', 'f2', 'f3']
        
        # Test with cutoff 1.0 (should include all)
        top_all = identify_top_descriptors(importances, cutoff=1.0)
        assert len(top_all) == 4

    def test_calculate_mae_degradation(self):
        """Test MAE degradation calculation."""
        base_mae = 5.0
        perturbed_mae = 7.5
        
        degradation = calculate_mae_degradation(base_mae, perturbed_mae)
        
        assert degradation == 50.0  # (7.5 - 5.0) / 5.0 * 100

    def test_verify_stability(self):
        """Test stability verification based on rank correlation."""
        # Test stable case (rho >= 0.9)
        is_stable = verify_stability(0.95)
        assert is_stable == True
        
        # Test unstable case (rho < 0.9)
        is_stable = verify_stability(0.85)
        assert is_stable == False
        
        # Test edge case (exactly 0.9)
        is_stable = verify_stability(0.90)
        assert is_stable == True

    @patch('sensitivity_analysis.load_model')
    @patch('sensitivity_analysis.load_data')
    @patch('sensitivity_analysis.extract_feature_importance')
    @patch('sensitivity_analysis.identify_top_descriptors')
    @patch('sensitivity_analysis.run_sensitivity_sweep')
    def test_run_sensitivity_analysis_full(
        self,
        mock_sweep,
        mock_identify,
        mock_extract,
        mock_load_data,
        mock_load_model,
        temp_dir
    ):
        """Test the full sensitivity analysis pipeline."""
        # Setup mocks
        mock_model = Mock()
        mock_model.feature_importances_ = np.array([0.5, 0.3, 0.2])
        mock_load_model.return_value = mock_model
        
        mock_load_data.return_value = (pd.DataFrame({'f1': [1, 2]}), pd.Series([1, 2]))
        
        mock_importances = pd.DataFrame({
            'rank': [1, 2, 3],
            'descriptor': ['f1', 'f2', 'f3'],
            'importance': [0.5, 0.3, 0.2],
            'cumulative_importance': [0.5, 0.8, 1.0]
        })
        mock_extract.return_value = mock_importances
        
        mock_identify.return_value = mock_importances.head(2)
        
        mock_sweep.return_value = pd.DataFrame({
            'noise_level': [0.01, 0.05],
            'cutoff': [0.1, 0.1],
            'top_3_descriptors': ['f1,f2,f3', 'f1,f2,f3'],
            'rank_correlation': [0.95, 0.85],
            'stable_flag': [True, False]
        })
        
        # Run the analysis
        from sensitivity_analysis import main
        
        # Mock argparse to simulate command line args
        with patch('sys.argv', ['sensitivity_analysis.py', '--output', temp_dir]):
            with patch('argparse.ArgumentParser.parse_args') as mock_args:
                mock_args.return_value = Mock(output=temp_dir, model_path='mock.pkl', data_path='mock.csv')
                
                # This would normally write files, but we're testing the logic flow
                # We just verify the mocks were called correctly
                pass
        
        # Verify the mocks were called
        mock_load_model.assert_called_once()
        mock_extract.assert_called_once()

    def test_prepare_features_target(self, mock_data):
        """Test feature and target preparation."""
        X, y = mock_data
        
        # This function essentially just returns the inputs, but validates types
        features, target = prepare_features_target(X, y)
        
        assert isinstance(features, pd.DataFrame)
        assert isinstance(target, pd.Series)
        assert features.shape[0] == target.shape[0]
        assert list(features.columns) == ['feature_1', 'feature_2', 'feature_3', 'feature_4']

    def test_load_model_from_file(self, temp_dir):
        """Test loading a model from a file."""
        # Create a mock model and save it
        import joblib
        mock_model = Mock()
        mock_model.feature_importances_ = np.array([0.5, 0.3, 0.2])
        
        model_path = Path(temp_dir) / "test_model.pkl"
        joblib.dump(mock_model, model_path)
        
        # Load it back
        loaded_model = load_model(str(model_path))
        
        assert loaded_model is not None
        assert np.allclose(loaded_model.feature_importances_, mock_model.feature_importances_)

    def test_load_data_from_csv(self, temp_dir, mock_data):
        """Test loading data from CSV files."""
        import joblib
        X, y = mock_data
        
        # Save to CSV
        X_path = Path(temp_dir) / "features.csv"
        y_path = Path(temp_dir) / "target.csv"
        
        X.to_csv(X_path, index=False)
        y.to_csv(y_path, index=False)
        
        # Load back
        loaded_X, loaded_y = load_data(str(X_path), str(y_path))
        
        assert loaded_X.shape == X.shape
        assert loaded_y.shape == y.shape
        assert np.allclose(loaded_X.values, X.values)
        assert np.allclose(loaded_y.values, y.values)

    def test_sensitivity_sweep_integration(self, mock_model, mock_data):
        """Test the sensitivity sweep logic with noise injection."""
        X, y = mock_data
        
        # Mock the training function to return consistent results
        def mock_train(X_train, y_train):
            m = Mock()
            # Return different importances based on noise level
            if np.any(X_train < 0):  # If noise was added
                m.feature_importances_ = np.array([0.4, 0.3, 0.2, 0.1])
            else:
                m.feature_importances_ = np.array([0.5, 0.3, 0.15, 0.05])
            return m
        
        with patch('sensitivity_analysis.train_model', side_effect=mock_train):
            results = run_sensitivity_sweep(
                mock_model, 
                X, 
                y, 
                noise_levels=[0.0, 0.05],
                cutoffs=[0.8],
                random_state=42
            )
            
            assert isinstance(results, pd.DataFrame)
            assert 'noise_level' in results.columns
            assert 'rank_correlation' in results.columns
            assert 'stable_flag' in results.columns
            assert len(results) == 2  # Two noise levels

    def test_generate_summary_report(self, temp_dir):
        """Test summary report generation."""
        # Create mock results
        importances = pd.DataFrame({
            'rank': [1, 2, 3, 4],
            'descriptor': ['f1', 'f2', 'f3', 'f4'],
            'importance': [0.5, 0.3, 0.15, 0.05],
            'cumulative_importance': [0.5, 0.8, 0.95, 1.0]
        })
        
        sweep_results = pd.DataFrame({
            'noise_level': [0.01, 0.05],
            'cutoff': [0.1, 0.1],
            'top_3_descriptors': ['f1,f2,f3', 'f1,f2,f3'],
            'rank_correlation': [0.95, 0.85],
            'stable_flag': [True, False]
        })
        
        output_path = Path(temp_dir) / "sensitivity_report.json"
        
        # This function should create a JSON summary
        generate_summary_report(importances, sweep_results, str(output_path))
        
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            report = json.load(f)
        
        assert 'top_descriptors' in report
        assert 'stability_summary' in report
        assert report['top_descriptors']['count'] == 4
        assert report['stability_summary']['stable_count'] == 1
        assert report['stability_summary']['total_count'] == 2