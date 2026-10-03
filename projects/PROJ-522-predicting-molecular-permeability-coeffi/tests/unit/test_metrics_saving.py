"""
Unit tests for metrics saving functionality (T022b).
"""
import os
import sys
import tempfile
import pandas as pd
import pytest
from pathlib import Path

# Add code to path if running standalone
code_path = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_path))

from utils.metrics import save_predictions, calculate_metrics


class TestSavePredictions:
    """Tests for the save_predictions function."""

    def test_save_predictions_creates_file(self, tmp_path):
        """Test that save_predictions creates the output file."""
        df = pd.DataFrame({
            'fold': [1, 2],
            'model': ['gcn', 'rf'],
            'r2': [0.85, 0.80],
            'mae': [0.12, 0.15],
            'rmse': [0.18, 0.20],
            'prediction': [1.1, 2.2],
            'target': [1.0, 2.0]
        })
        output_path = tmp_path / "predictions.csv"
        
        save_predictions(df, str(output_path))
        
        assert output_path.exists()
        loaded_df = pd.read_csv(output_path)
        assert len(loaded_df) == 2

    def test_save_predictions_correct_schema(self, tmp_path):
        """Test that the saved file has the correct columns."""
        df = pd.DataFrame({
            'fold': [1],
            'model': ['gcn'],
            'r2': [0.85],
            'mae': [0.12],
            'rmse': [0.18],
            'prediction': [1.1],
            'target': [1.0]
        })
        output_path = tmp_path / "predictions.csv"
        
        save_predictions(df, str(output_path))
        
        loaded_df = pd.read_csv(output_path)
        expected_cols = ['fold', 'model', 'r2', 'mae', 'rmse', 'prediction', 'target']
        assert list(loaded_df.columns) == expected_cols

    def test_save_predictions_missing_columns_raises(self, tmp_path):
        """Test that missing required columns raise an error."""
        df = pd.DataFrame({
            'fold': [1],
            'model': ['gcn'],
            'r2': [0.85]
        })
        output_path = tmp_path / "predictions.csv"
        
        with pytest.raises(ValueError, match="Missing required columns"):
            save_predictions(df, str(output_path))

    def test_save_predictions_creates_parent_dir(self, tmp_path):
        """Test that parent directories are created if they don't exist."""
        df = pd.DataFrame({
            'fold': [1],
            'model': ['gcn'],
            'r2': [0.85],
            'mae': [0.12],
            'rmse': [0.18],
            'prediction': [1.1],
            'target': [1.0]
        })
        output_path = tmp_path / "subdir" / "predictions.csv"
        
        save_predictions(df, str(output_path))
        
        assert output_path.exists()

    def test_save_predictions_data_integrity(self, tmp_path):
        """Test that data is preserved correctly after saving and loading."""
        df = pd.DataFrame({
            'fold': [1, 2, 3],
            'model': ['gcn', 'rf', 'lr'],
            'r2': [0.85, 0.80, 0.78],
            'mae': [0.12, 0.15, 0.16],
            'rmse': [0.18, 0.20, 0.21],
            'prediction': [1.1, 2.2, 3.3],
            'target': [1.0, 2.0, 3.0]
        })
        output_path = tmp_path / "predictions.csv"
        
        save_predictions(df, str(output_path))
        loaded_df = pd.read_csv(output_path)
        
        # Check data types and values
        assert loaded_df['fold'].tolist() == [1, 2, 3]
        assert loaded_df['model'].tolist() == ['gcn', 'rf', 'lr']
        assert loaded_df['r2'].tolist() == [0.85, 0.80, 0.78]


class TestCalculateMetrics:
    """Tests for the calculate_metrics function."""

    def test_calculate_metrics_basic(self):
        """Test basic metric calculation."""
        y_true = [1.0, 2.0, 3.0, 4.0, 5.0]
        y_pred = [1.1, 2.1, 2.9, 4.1, 5.0]
        
        metrics = calculate_metrics(y_true, y_pred)
        
        assert 'r2' in metrics
        assert 'mae' in metrics
        assert 'rmse' in metrics
        assert 0.0 <= metrics['r2'] <= 1.0
        assert metrics['mae'] >= 0
        assert metrics['rmse'] >= 0

    def test_calculate_metrics_perfect_prediction(self):
        """Test metrics for perfect predictions."""
        y_true = [1.0, 2.0, 3.0]
        y_pred = [1.0, 2.0, 3.0]
        
        metrics = calculate_metrics(y_true, y_pred)
        
        assert metrics['r2'] == 1.0
        assert metrics['mae'] == 0.0
        assert metrics['rmse'] == 0.0

    def test_calculate_metrics_numpy_arrays(self):
        """Test that numpy arrays are handled correctly."""
        import numpy as np
        y_true = np.array([1.0, 2.0, 3.0])
        y_pred = np.array([1.1, 2.1, 2.9])
        
        metrics = calculate_metrics(y_true, y_pred)
        
        assert 'r2' in metrics
        assert metrics['mae'] >= 0