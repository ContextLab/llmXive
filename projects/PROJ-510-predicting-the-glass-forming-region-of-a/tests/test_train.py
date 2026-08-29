import pytest
import json
import os
import sys
import numpy as np
from unittest.mock import patch, MagicMock
import pandas as pd

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from train import load_data, train_model, generate_null_distribution, run_training
from contracts.model_output.schema import ModelMetrics

# Mock data for testing
MOCK_DATA = pd.DataFrame({
    'mixing_enthalpy': np.random.rand(100),
    'atomic_size_mismatch': np.random.rand(100),
    'electronegativity_variance': np.random.rand(100),
    'critical_cooling_rate': np.random.rand(100) * 1000
})

@pytest.fixture
def mock_data_file(tmp_path):
    file_path = tmp_path / "processed_alloys.csv"
    MOCK_DATA.to_csv(file_path, index=False)
    return str(file_path)

@pytest.fixture
def mock_model_output(tmp_path):
    output_dir = tmp_path / "models"
    output_dir.mkdir()
    return str(output_dir)

def test_load_data(mock_data_file):
    """Test loading data from CSV."""
    df = load_data(mock_data_file)
    assert df is not None
    assert len(df) == 100
    assert 'critical_cooling_rate' in df.columns

def test_train_model_structure(mock_data_file, mock_model_output):
    """Test that training produces a valid ModelMetrics structure."""
    # Mock the actual training to avoid heavy computation in unit test
    # but ensure the output structure is correct
    with patch('train.RandomForestRegressor') as mock_rf:
        mock_rf_instance = MagicMock()
        mock_rf_instance.predict.return_value = np.random.rand(20)
        mock_rf.return_value = mock_rf_instance

        with patch('train.cross_val_score') as mock_cv:
            mock_cv.return_value = np.array([0.8, 0.85, 0.82, 0.79, 0.81])

            metrics = train_model(mock_data_file, mock_model_output)

            assert metrics is not None
            assert isinstance(metrics, dict)
            assert 'fold_scores' in metrics
            assert 'mean_rmse' in metrics
            assert 'test_rmse' in metrics
            assert 'feature_importance_ranking' in metrics
            assert 'p_value_vs_null' in metrics

            # Validate types
            assert isinstance(metrics['fold_scores'], list)
            assert len(metrics['fold_scores']) == 5
            assert isinstance(metrics['mean_rmse'], (int, float))
            assert isinstance(metrics['test_rmse'], (int, float))

def test_model_metrics_schema_compliance(mock_data_file, mock_model_output):
    """Integration test: Ensure the produced metrics adhere to ModelMetrics schema."""
    # We simulate the full training flow but mock the heavy lifting
    # to ensure the schema is respected.
    
    with patch('train.RandomForestRegressor') as mock_rf:
        mock_rf_instance = MagicMock()
        mock_rf_instance.predict.return_value = np.random.rand(20)
        mock_rf.return_value = mock_rf_instance

        with patch('train.cross_val_score') as mock_cv:
            mock_cv.return_value = np.array([0.8, 0.85, 0.82, 0.79, 0.81])
            
            with patch('train.ttest_ind') as mock_ttest:
                mock_ttest.return_value = (2.5, 0.01) # statistic, p-value

                metrics = train_model(mock_data_file, mock_model_output)
                
                # Try to validate against schema (conceptually)
                # Since we don't have the actual pydantic model loaded here easily without imports
                # we check the keys manually as per the schema definition in tasks.md
                required_keys = ['fold_scores', 'mean_rmse', 'test_rmse', 'feature_importance_ranking', 'p_value_vs_null']
                for key in required_keys:
                    assert key in metrics, f"Missing required key in ModelMetrics: {key}"
                
                # Check array types
                assert isinstance(metrics['fold_scores'], list)
                assert isinstance(metrics['feature_importance_ranking'], list)
                
                # Check numeric types
                assert isinstance(metrics['mean_rmse'], (int, float))
                assert isinstance(metrics['test_rmse'], (int, float))
                assert isinstance(metrics['p_value_vs_null'], (int, float))

def test_run_training_integration(mock_data_file, mock_model_output):
    """Integration test for the full run_training pipeline producing valid files."""
    # Mock the heavy parts
    with patch('train.RandomForestRegressor') as mock_rf:
        mock_rf_instance = MagicMock()
        mock_rf_instance.predict.return_value = np.random.rand(20)
        mock_rf.return_value = mock_rf_instance

        with patch('train.cross_val_score') as mock_cv:
            mock_cv.return_value = np.array([0.8, 0.85, 0.82, 0.79, 0.81])
            
            with patch('train.ttest_ind') as mock_ttest:
                mock_ttest.return_value = (2.5, 0.01)

                run_training(mock_data_file, mock_model_output)
                
                # Check that files were created
                assert os.path.exists(os.path.join(mock_model_output, "cv_metrics.json"))
                assert os.path.exists(os.path.join(mock_model_output, "random_forest_model.pkl"))
                assert os.path.exists(os.path.join(mock_model_output, "statistical_comparison.json"))
                
                # Validate JSON content
                with open(os.path.join(mock_model_output, "cv_metrics.json")) as f:
                    cv_data = json.load(f)
                    assert 'fold_scores' in cv_data
                    assert 'mean_rmse' in cv_data

                with open(os.path.join(mock_model_output, "statistical_comparison.json")) as f:
                    stat_data = json.load(f)
                    assert 'p_value' in stat_data
                    assert 'test_statistic' in stat_data
