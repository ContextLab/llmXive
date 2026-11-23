import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.baseline.calculate_metrics import calculate_metrics, calculate_auc_roc, main

class TestT028MetricsCalculation:
    """Test suite for T028: Baseline metrics calculation."""

    def test_calculate_metrics_basic(self):
        """Test basic metric calculation with known values."""
        # Create simple test data
        ground_truth = [
            {"is_critical": True},
            {"is_critical": False},
            {"is_critical": True},
            {"is_critical": False},
            {"is_critical": True}
        ]
        predictions = [
            {"is_critical": True},
            {"is_critical": False},
            {"is_critical": True},
            {"is_critical": True},  # False positive
            {"is_critical": True}
        ]
        
        metrics = calculate_metrics(predictions, ground_truth)
        
        # Expected: TP=3, TN=1, FP=1, FN=0
        # Precision = 3/4 = 0.75
        # Recall = 3/3 = 1.0
        # F1 = 2 * 0.75 * 1.0 / (0.75 + 1.0) = 1.5 / 1.75 = 0.8571
        assert metrics['true_positives'] == 3
        assert metrics['true_negatives'] == 1
        assert metrics['false_positives'] == 1
        assert metrics['false_negatives'] == 0
        assert abs(metrics['precision'] - 0.75) < 0.001
        assert metrics['recall'] == 1.0
        assert abs(metrics['f1_score'] - 0.8571) < 0.001

    def test_calculate_metrics_edge_cases(self):
        """Test edge cases: all positive, all negative, empty."""
        # All positive, all predicted positive
        gt_all_pos = [{"is_critical": True}, {"is_critical": True}]
        pred_all_pos = [{"is_critical": True}, {"is_critical": True}]
        metrics = calculate_metrics(pred_all_pos, gt_all_pos)
        assert metrics['f1_score'] == 1.0
        assert metrics['auc_roc'] == 1.0
        
        # All negative, all predicted negative
        gt_all_neg = [{"is_critical": False}, {"is_critical": False}]
        pred_all_neg = [{"is_critical": False}, {"is_critical": False}]
        metrics = calculate_metrics(pred_all_neg, gt_all_neg)
        assert metrics['f1_score'] == 0.0  # No positives to detect
        assert metrics['auc_roc'] == 1.0
        
        # Empty case
        metrics = calculate_metrics([], [])
        assert metrics['f1_score'] == 0.0
        assert metrics['auc_roc'] == 0.0

    def test_mismatched_counts_raises_error(self):
        """Test that mismatched prediction and ground truth counts raise error."""
        gt = [{"is_critical": True}, {"is_critical": False}]
        pred = [{"is_critical": True}]
        
        with pytest.raises(ValueError, match="Prediction count.*does not match"):
            calculate_metrics(pred, gt)

    def test_interruption_reduction_calculation(self):
        """Test interruption reduction rate calculation."""
        # Scenario: 10 actual critical events, model predicts 8 (6 TP, 2 FP)
        # Baseline interruptions = 10 (all actual critical)
        # Actual interruptions = 8 (all predicted critical)
        # Reduction = (10 - 8) / 10 = 0.2
        
        gt = [{"is_critical": True}] * 10
        pred = [{"is_critical": True}] * 6 + [{"is_critical": False}] * 2 + [{"is_critical": True}] * 2
        # Wait, let's be more explicit:
        # 10 actual critical: [T, T, T, T, T, T, T, T, T, T]
        # Predictions: [T, T, T, T, T, T, F, F, T, T] -> 8 predicted critical
        # TP = 8, FN = 2, FP = 0
        # Actually, let's construct it properly:
        gt = [{"is_critical": True} for _ in range(10)]
        pred = [{"is_critical": True} for _ in range(8)] + [{"is_critical": False} for _ in range(2)]
        
        # But we need to match indices. Let's do:
        gt = [{"is_critical": True}, {"is_critical": True}, {"is_critical": True}, 
              {"is_critical": True}, {"is_critical": True}, {"is_critical": True},
              {"is_critical": True}, {"is_critical": True}, {"is_critical": True},
              {"is_critical": True}]
        
        pred = [{"is_critical": True}, {"is_critical": True}, {"is_critical": True},
                {"is_critical": True}, {"is_critical": True}, {"is_critical": True},
                {"is_critical": True}, {"is_critical": True}, {"is_critical": False},
                {"is_critical": False}]
        
        # TP=8, FN=2, FP=0
        # Baseline = 10, Actual = 8
        # Reduction = (10-8)/10 = 0.2
        
        metrics = calculate_metrics(pred, gt)
        assert metrics['true_positives'] == 8
        assert metrics['false_negatives'] == 2
        assert metrics['false_positives'] == 0
        assert abs(metrics['interruption_reduction_rate'] - 0.2) < 0.001

    def test_auc_roc_calculation(self):
        """Test AUC-ROC calculation."""
        # Perfect classifier
        y_true = [0, 0, 0, 1, 1, 1]
        y_pred = [0, 0, 0, 1, 1, 1]
        auc = calculate_auc_roc(y_true, y_pred)
        assert auc == 1.0
        
        # Random classifier (approximately 0.5)
        y_true = [0, 1, 0, 1, 0, 1]
        y_pred = [0, 1, 1, 0, 0, 1]
        auc = calculate_auc_roc(y_true, y_pred)
        # Should be close to 0.5 for random
        assert 0.3 < auc < 0.7

    @patch('src.baseline.calculate_metrics.load_predictions')
    @patch('src.baseline.calculate_metrics.load_ground_truth')
    @patch('src.baseline.calculate_metrics.logger')
    def test_main_function_execution(self, mock_logger, mock_load_gt, mock_load_pred):
        """Test the main function execution path."""
        # Setup mocks
        mock_gt_data = [{"is_critical": True}, {"is_critical": False}]
        mock_pred_data = [{"is_critical": True}, {"is_critical": False}]
        
        mock_load_gt.return_value = mock_gt_data
        mock_load_pred.return_value = mock_pred_data
        
        # Mock file existence
        with patch('pathlib.Path.exists', return_value=True):
            with patch('pathlib.Path.mkdir'):
                with patch('builtins.open', mock.mock_open()) as mock_file:
                    main()
                    
                    # Verify files were opened for writing
                    assert mock_file.called

    def test_metrics_json_structure(self):
        """Test that the metrics dictionary has the expected structure."""
        gt = [{"is_critical": True}, {"is_critical": False}]
        pred = [{"is_critical": True}, {"is_critical": False}]
        
        metrics = calculate_metrics(pred, gt)
        
        required_keys = [
            'f1_score', 'auc_roc', 'interruption_reduction_rate',
            'precision', 'recall', 'accuracy',
            'true_positives', 'true_negatives', 'false_positives',
            'false_negatives', 'total_samples'
        ]
        
        for key in required_keys:
            assert key in metrics, f"Missing key: {key}"
            assert isinstance(metrics[key], (int, float)), f"Key {key} should be numeric"