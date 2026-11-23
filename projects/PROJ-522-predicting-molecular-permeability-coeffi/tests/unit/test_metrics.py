"""
Unit tests for metric aggregation in code/metrics.py
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import tempfile
import os
import sys

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.metrics import calculate_metrics, aggregate_fold_metrics, save_predictions

class TestCalculateMetrics:
    def test_basic_metrics(self):
        """Test basic metric calculation."""
        y_true = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        y_pred = np.array([1.1, 2.1, 2.9, 4.2, 4.8])
        
        metrics = calculate_metrics(y_true, y_pred)
        
        assert 'r2' in metrics
        assert 'mae' in metrics
        assert 'rmse' in metrics
        assert 0.9 < metrics['r2'] < 1.0  # High R2 for close predictions
        assert metrics['mae'] > 0
        assert metrics['rmse'] > 0

    def test_perfect_prediction(self):
        """Test perfect prediction yields R2=1.0, MAE=0, RMSE=0."""
        y_true = np.array([1.0, 2.0, 3.0])
        y_pred = np.array([1.0, 2.0, 3.0])
        
        metrics = calculate_metrics(y_true, y_pred)
        
        assert np.isclose(metrics['r2'], 1.0)
        assert np.isclose(metrics['mae'], 0.0)
        assert np.isclose(metrics['rmse'], 0.0)

    def test_empty_array_raises(self):
        """Test that empty arrays raise ValueError."""
        with pytest.raises(ValueError):
            calculate_metrics(np.array([]), np.array([]))

    def test_single_value(self):
        """Test single value prediction."""
        y_true = np.array([5.0])
        y_pred = np.array([5.0])
        
        metrics = calculate_metrics(y_true, y_pred)
        assert np.isclose(metrics['r2'], 1.0)

class TestAggregateFoldMetrics:
    def test_aggregate_multiple_folds(self):
        """Test aggregation across multiple folds."""
        metrics_list = [
            {'r2': 0.8, 'mae': 0.5, 'rmse': 0.6},
            {'r2': 0.7, 'mae': 0.6, 'rmse': 0.7},
            {'r2': 0.9, 'mae': 0.4, 'rmse': 0.5}
        ]
        
        aggregated = aggregate_fold_metrics(metrics_list)
        
        assert 'mean' in aggregated
        assert 'std' in aggregated
        assert np.isclose(aggregated['mean']['r2'], (0.8 + 0.7 + 0.9) / 3)
        assert np.isclose(aggregated['mean']['mae'], (0.5 + 0.6 + 0.4) / 3)

    def test_single_fold(self):
        """Test aggregation with a single fold."""
        metrics_list = [{'r2': 0.85, 'mae': 0.55, 'rmse': 0.65}]
        
        aggregated = aggregate_fold_metrics(metrics_list)
        
        assert aggregated['mean']['r2'] == 0.85
        assert aggregated['std']['r2'] == 0.0  # Std of single value is 0

    def test_empty_list_raises(self):
        """Test that empty list raises ValueError."""
        with pytest.raises(ValueError):
            aggregate_fold_metrics([])

class TestSavePredictions:
    def test_save_predictions_creates_file(self):
        """Test that save_predictions creates the file correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "predictions.csv")
            
            df = pd.DataFrame({
                'smiles': ['CCO', 'CCCO'],
                'true': [1.0, 2.0],
                'pred': [1.1, 2.1],
                'fold': [0, 0]
            })
            
            save_predictions(df, output_path)
            
            assert os.path.exists(output_path)
            loaded_df = pd.read_csv(output_path)
            assert len(loaded_df) == 2
            assert list(loaded_df.columns) == ['smiles', 'true', 'pred', 'fold']

    def test_save_predictions_creates_directories(self):
        """Test that save_predictions creates parent directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "subdir", "predictions.csv")
            
            df = pd.DataFrame({
                'smiles': ['CCO'],
                'true': [1.0],
                'pred': [1.1],
                'fold': [0]
            })
            
            save_predictions(df, output_path)
            
            assert os.path.exists(output_path)

    def test_save_predictions_with_fold_index(self):
        """Test that save_predictions adds fold index if missing in DF."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "predictions.csv")
            
            df = pd.DataFrame({
                'smiles': ['CCO'],
                'true': [1.0],
                'pred': [1.1]
                # No 'fold' column
            })
            
            save_predictions(df, output_path, fold_index=2)
            
            loaded_df = pd.read_csv(output_path)
            assert 'fold' in loaded_df.columns
            assert loaded_df['fold'].iloc[0] == 2