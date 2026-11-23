"""
Unit tests for the Random Forest baseline model.
"""
import pytest
import numpy as np
import pandas as pd
from unittest.mock import patch, MagicMock
import tempfile
from pathlib import Path

from models.baseline import (
    extract_topological_features,
    train_baseline_model,
    evaluate_model,
    load_processed_data_for_baseline,
)
from models.evaluation_result import EvaluationResult


class TestExtractTopologicalFeatures:
    """Tests for feature extraction from SMILES."""
    
    def test_valid_smiles(self):
        """Test extraction from valid SMILES strings."""
        smiles_list = [
            "CCO",  # Ethanol
            "c1ccccc1",  # Benzene
            "CC(=O)O",  # Acetic acid
        ]
        
        df = extract_topological_features(smiles_list)
        
        assert len(df) == 3
        assert 'smiles' in df.columns
        assert 'total_atoms' in df.columns
        assert 'num_rings' in df.columns
        assert 'mol_logp' in df.columns
        
        # Check specific values
        assert df.loc[df['smiles'] == 'c1ccccc1', 'num_aromatic_rings'].iloc[0] == 1
        assert df.loc[df['smiles'] == 'CCO', 'num_rings'].iloc[0] == 0
    
    def test_invalid_smiles_handling(self):
        """Test handling of invalid SMILES."""
        smiles_list = [
            "CCO",
            "invalid_smiles_123",
            "c1ccccc1",
        ]
        
        df = extract_topological_features(smiles_list)
        
        # Should skip invalid SMILES
        assert len(df) == 2
        assert "invalid_smiles_123" not in df['smiles'].values
    
    def test_high_failure_rate_raises(self):
        """Test that high failure rate raises ValueError."""
        smiles_list = ["invalid1", "invalid2", "invalid3", "invalid4", "invalid5"]
        
        with pytest.raises(ValueError, match="Failed to process"):
            extract_topological_features(smiles_list)

class TestTrainBaselineModel:
    """Tests for model training."""
    
    def test_training_produces_model(self):
        """Test that training produces a valid model."""
        X_train = np.random.rand(100, 10)
        y_train = np.random.rand(100)
        X_val = np.random.rand(20, 10)
        y_val = np.random.rand(20)
        
        model, metrics = train_baseline_model(X_train, y_train, X_val, y_val)
        
        assert model is not None
        assert hasattr(model, 'predict')
        assert 'mae' in metrics
        assert 'rmse' in metrics
        assert 'r2' in metrics
        assert metrics['mae'] >= 0
        assert metrics['rmse'] >= 0
        assert -np.inf < metrics['r2'] <= 1.0
    
    def test_different_n_estimators(self):
        """Test training with different numbers of estimators."""
        X_train = np.random.rand(50, 5)
        y_train = np.random.rand(50)
        X_val = np.random.rand(10, 5)
        y_val = np.random.rand(10)
        
        model_10, _ = train_baseline_model(X_train, y_train, X_val, y_val, n_estimators=10)
        model_100, _ = train_baseline_model(X_train, y_train, X_val, y_val, n_estimators=100)
        
        assert model_10.n_estimators == 10
        assert model_100.n_estimators == 100

class TestEvaluateModel:
    """Tests for model evaluation."""
    
    def test_evaluation_returns_result(self):
        """Test that evaluation returns an EvaluationResult."""
        from sklearn.ensemble import RandomForestRegressor
        
        model = RandomForestRegressor(n_estimators=10, random_state=42)
        X_test = np.random.rand(20, 5)
        y_test = np.random.rand(20)
        
        # Train a simple model first
        model.fit(np.random.rand(50, 5), np.random.rand(50))
        
        result = evaluate_model(model, X_test, y_test)
        
        assert isinstance(result, EvaluationResult)
        assert result.model_type == "RandomForest"
        assert 'mae' in result.metrics
        assert 'rmse' in result.metrics
        assert 'r2' in result.metrics
        assert len(result.predictions) == 20
        assert len(result.actuals) == 20
    
    def test_metrics_consistency(self):
        """Test that metrics are consistent with sklearn."""
        from sklearn.ensemble import RandomForestRegressor
        from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
        
        model = RandomForestRegressor(n_estimators=10, random_state=42)
        X_test = np.random.rand(20, 5)
        y_test = np.random.rand(20)
        
        model.fit(np.random.rand(50, 5), np.random.rand(50))
        
        result = evaluate_model(model, X_test, y_test)
        
        y_pred = model.predict(X_test)
        
        assert np.isclose(result.metrics['mae'], mean_absolute_error(y_test, y_pred))
        assert np.isclose(result.metrics['rmse'], np.sqrt(mean_squared_error(y_test, y_pred)))
        assert np.isclose(result.metrics['r2'], r2_score(y_test, y_pred))

class TestLoadProcessedDataForBaseline:
    """Tests for data loading."""
    
    @patch('models.baseline.get_data_dir')
    @patch('pandas.read_parquet')
    def test_load_with_existing_data(self, mock_read_parquet, mock_get_data_dir):
        """Test loading when processed data exists."""
        # Mock the data directory
        mock_get_data_dir.return_value = Path("/fake/data")
        
        # Create mock dataframe
        mock_df = pd.DataFrame({
            'smiles': ['CCO', 'c1ccccc1'],
            'surface_area': [20.0, 50.0],
            'mol_logp': [0.5, 2.0],
            'tpsa': [20.0, 0.0],
            'total_atoms': [3, 6],
        })
        mock_read_parquet.return_value = mock_df
        
        X, y = load_processed_data_for_baseline()
        
        assert isinstance(X, pd.DataFrame)
        assert isinstance(y, pd.Series)
        assert len(X) == 2
        assert len(y) == 2
        assert 'surface_area' not in X.columns
        assert 'smiles' not in X.columns
        assert np.allclose(y.values, [20.0, 50.0])
    
    @patch('models.baseline.get_data_dir')
    def test_missing_data_raises(self, mock_get_data_dir):
        """Test that missing data raises FileNotFoundError."""
        mock_get_data_dir.return_value = Path("/fake/data")
        
        with patch('pathlib.Path.exists', return_value=False):
            with pytest.raises(FileNotFoundError, match="Processed data not found"):
                load_processed_data_for_baseline()