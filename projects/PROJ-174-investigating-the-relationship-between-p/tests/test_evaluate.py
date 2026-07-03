import os
import sys
import tempfile
import pandas as pd
import numpy as np
import pytest
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from classification.evaluate import load_held_out_data, compute_metrics, evaluate_held_out

class TestEvaluate:
    
    def test_load_held_out_data_valid(self):
        """Test loading a valid held-out dataset."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df = pd.DataFrame({
                'predicted_prob': [0.1, 0.9, 0.4, 0.6],
                'label': [0, 1, 0, 1]
            })
            df.to_csv(f, index=False)
            temp_path = f.name
        
        try:
            loaded = load_held_out_data(temp_path)
            assert loaded.shape == (4, 2)
            assert list(loaded.columns) == ['predicted_prob', 'label']
            assert loaded['label'].dtype in [np.int64, np.float64, int, float]
        finally:
            os.unlink(temp_path)

    def test_load_held_out_data_missing_columns(self):
        """Test that missing columns raise ValueError."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df = pd.DataFrame({
                'predicted_prob': [0.1, 0.9],
                'wrong_col': [0, 1]
            })
            df.to_csv(f, index=False)
            temp_path = f.name
        
        try:
            with pytest.raises(ValueError):
                load_held_out_data(temp_path)
        finally:
            os.unlink(temp_path)

    def test_compute_metrics_basic(self):
        """Test basic metric computation."""
        y_true = np.array([0, 1, 0, 1, 0, 1])
        y_pred = np.array([0, 1, 0, 1, 1, 0]) # 2 errors
        y_prob = np.array([0.1, 0.9, 0.2, 0.8, 0.6, 0.4])
        
        metrics = compute_metrics(y_true, y_pred, y_prob)
        
        assert 'accuracy' in metrics
        assert 'precision' in metrics
        assert 'recall' in metrics
        assert 'roc_auc' in metrics
        
        # Accuracy: 4 correct out of 6
        assert metrics['accuracy'] == 4/6
        
        # Precision: TP / (TP + FP) -> 2 / (2 + 1) = 0.666...
        # Recall: TP / (TP + FN) -> 2 / (2 + 1) = 0.666...
        assert abs(metrics['precision'] - 2/3) < 0.001
        assert abs(metrics['recall'] - 2/3) < 0.001
        
        # ROC AUC should be valid since we have both classes
        assert 0.5 <= metrics['roc_auc'] <= 1.0

    def test_compute_metrics_single_class(self):
        """Test handling of single class in y_true (ROC-AUC undefined)."""
        y_true = np.array([1, 1, 1, 1])
        y_pred = np.array([1, 1, 1, 1])
        y_prob = np.array([0.9, 0.8, 0.9, 0.7])
        
        metrics = compute_metrics(y_true, y_pred, y_prob)
        
        assert metrics['roc_auc'] is np.nan or np.isnan(metrics['roc_auc'])
        assert metrics['accuracy'] == 1.0
        
    def test_evaluate_held_out_integration(self):
        """Integration test for the full evaluation flow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, 'input.csv')
            output_path = os.path.join(tmpdir, 'output.csv')
            
            # Create input data
            df = pd.DataFrame({
                'predicted_prob': [0.1, 0.2, 0.8, 0.9, 0.4, 0.6],
                'label': [0, 0, 1, 1, 1, 0] # 2 errors (0.4->1, 0.6->0)
            })
            df.to_csv(input_path, index=False)
            
            # Run evaluation
            evaluate_held_out(input_path, output_path)
            
            # Verify output file exists
            assert os.path.exists(output_path)
            
            # Verify content
            result_df = pd.read_csv(output_path)
            assert 'accuracy' in result_df.columns
            assert 'precision' in result_df.columns
            assert 'recall' in result_df.columns
            assert 'roc_auc' in result_df.columns
            
            # Check accuracy (4/6 correct)
            assert abs(result_df.iloc[0]['accuracy'] - 4/6) < 0.001