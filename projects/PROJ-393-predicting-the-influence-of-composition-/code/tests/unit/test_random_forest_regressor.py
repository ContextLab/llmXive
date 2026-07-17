import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os
import sys
from unittest.mock import patch, MagicMock

# Add code/src to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / 'src'))

from src.models.random_forest_regressor import (
    load_features_data,
    prepare_data,
    evaluate_model,
    run_random_forest_regression
)

class TestLoadFeaturesData:
    def test_load_valid_csv(self, tmp_path):
        """Test loading a valid CSV file."""
        data = {
            'Co2MnGa': [1.0],
            'avg_electronegativity': [1.8],
            'vec': [8.0],
            'coercivity_Oe': [10.0]
        }
        df = pd.DataFrame(data)
        csv_path = tmp_path / "test_features.csv"
        df.to_csv(csv_path, index=False)
        
        loaded_df = load_features_data(csv_path)
        assert len(loaded_df) == 1
        assert 'coercivity_Oe' in loaded_df.columns

    def test_file_not_found(self, tmp_path):
        """Test that FileNotFoundError is raised for missing file."""
        non_existent = tmp_path / "does_not_exist.csv"
        with pytest.raises(FileNotFoundError):
            load_features_data(non_existent)

class TestPrepareData:
    def test_prepare_data_shapes(self, tmp_path):
        """Test that X and y are correctly shaped."""
        data = {
            'feature1': [1.0, 2.0, 3.0],
            'feature2': [4.0, 5.0, 6.0],
            'coercivity_Oe': [10.0, 20.0, 30.0]
        }
        df = pd.DataFrame(data)
        
        X, y, feature_names = prepare_data(df, 'coercivity_Oe')
        
        assert X.shape == (3, 2)
        assert y.shape == (3,)
        assert 'feature1' in feature_names
        assert 'feature2' in feature_names

    def test_no_features_error(self, tmp_path):
        """Test that ValueError is raised if no features found."""
        data = {
            'coercivity_Oe': [10.0, 20.0]
        }
        df = pd.DataFrame(data)
        
        with pytest.raises(ValueError, match="No numeric feature columns"):
            prepare_data(df, 'coercivity_Oe')

class TestEvaluateModel:
    def test_evaluate_metrics(self):
        """Test that evaluation returns correct metrics."""
        # Mock model that predicts perfectly
        class MockModel:
            def predict(self, X):
                return X[:, 0]  # Just return first feature as prediction
        
        X = np.array([[10.0], [20.0], [30.0]])
        y = np.array([10.0, 20.0, 30.0])
        
        metrics = evaluate_model(MockModel(), X, y)
        
        assert 'r2' in metrics
        assert 'mae' in metrics
        assert metrics['r2'] == 1.0  # Perfect prediction
        assert metrics['mae'] == 0.0

class TestRunRandomForestRegression:
    def test_full_pipeline_integration(self, tmp_path):
        """Test the full pipeline with dummy data."""
        # Create dummy input data
        data = {
            'avg_electronegativity': [1.8, 1.9, 2.0, 2.1, 2.2],
            'vec': [8.0, 8.5, 9.0, 9.5, 10.0],
            'atomic_radii_variance': [0.01, 0.02, 0.03, 0.04, 0.05],
            'avg_d_electrons': [7.0, 7.5, 8.0, 8.5, 9.0],
            'atomic_size_mismatch': [0.02, 0.03, 0.04, 0.05, 0.06],
            'coercivity_Oe': [10.0, 15.0, 20.0, 25.0, 30.0]
        }
        df = pd.DataFrame(data)
        input_path = tmp_path / "alloys_features.csv"
        df.to_csv(input_path, index=False)
        
        model_dir = tmp_path / "models"
        metrics_path = tmp_path / "metrics.json"
        
        # Run pipeline (with reduced grid for speed)
        with patch('src.models.random_forest_regressor.tune_hyperparameters') as mock_tune:
            # Mock the tuning to return a simple model quickly
            mock_model = MagicMock()
            mock_model.predict.return_value = np.array([10.0, 15.0, 20.0, 25.0, 30.0])
            mock_tune.return_value = (mock_model, {'regressor__n_estimators': 10})
            
            model, metrics, params = run_random_forest_regression(
                input_path, model_dir, metrics_path
            )
            
            assert model is not None
            assert 'r2' in metrics
            assert 'mae' in metrics
            assert metrics_path.exists()