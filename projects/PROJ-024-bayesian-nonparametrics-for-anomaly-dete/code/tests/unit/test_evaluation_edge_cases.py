"""
Unit tests for evaluation metrics edge cases.

Tests cover:
- Empty predictions/labels
- All positive/negative cases
- Extreme precision/recall scenarios
- AUC calculation edge cases
"""
import pytest
import numpy as np
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from evaluation.metrics import (
    EvaluationMetrics, compute_f1_score, compute_precision,
    compute_recall, compute_auc, generate_confusion_matrix,
    compute_all_metrics, compute_roc_curve_points, compute_pr_curve_points
)


class TestEvaluationEdgeCases:
    """Test evaluation metrics edge cases."""
    
    def test_empty_predictions(self):
        """Test with empty prediction arrays."""
        y_true = np.array([])
        y_pred = np.array([])
        
        metrics = compute_all_metrics(y_true, y_pred)
        assert metrics.f1_score == 0.0
        assert metrics.precision == 0.0
        assert metrics.recall == 0.0
    
    def test_all_true_all_pred_positive(self):
        """Test with all true positives."""
        y_true = np.array([1, 1, 1, 1, 1])
        y_pred = np.array([1, 1, 1, 1, 1])
        
        metrics = compute_all_metrics(y_true, y_pred)
        assert metrics.f1_score == 1.0
        assert metrics.precision == 1.0
        assert metrics.recall == 1.0
    
    def test_all_true_all_pred_negative(self):
        """Test with all true negatives."""
        y_true = np.array([0, 0, 0, 0, 0])
        y_pred = np.array([0, 0, 0, 0, 0])
        
        metrics = compute_all_metrics(y_true, y_pred)
        assert metrics.f1_score == 0.0
        assert metrics.precision == 0.0
        assert metrics.recall == 0.0
    
    def test_all_true_some_pred_positive(self):
        """Test with all actual positives, some predicted positive."""
        y_true = np.array([1, 1, 1, 1, 1])
        y_pred = np.array([1, 0, 1, 0, 1])
        
        metrics = compute_all_metrics(y_true, y_pred)
        assert metrics.precision == 1.0
        assert metrics.recall == 0.6
        assert metrics.f1_score > 0.0
    
    def test_all_pred_positive_no_true(self):
        """Test with all predicted positive but no actual positives."""
        y_true = np.array([0, 0, 0, 0, 0])
        y_pred = np.array([1, 1, 1, 1, 1])
        
        metrics = compute_all_metrics(y_true, y_pred)
        assert metrics.precision == 0.0
        assert metrics.recall == 0.0
        assert metrics.f1_score == 0.0
    
    def test_single_sample(self):
        """Test with single sample."""
        y_true = np.array([1])
        y_pred = np.array([1])
        
        metrics = compute_all_metrics(y_true, y_pred)
        assert metrics.f1_score == 1.0
    
    def test_single_sample_mismatch(self):
        """Test with single sample mismatch."""
        y_true = np.array([1])
        y_pred = np.array([0])
        
        metrics = compute_all_metrics(y_true, y_pred)
        assert metrics.f1_score == 0.0
    
    def test_precision_division_by_zero(self):
        """Test precision when no positive predictions."""
        y_true = np.array([1, 1, 0, 0])
        y_pred = np.array([0, 0, 0, 0])
        
        precision = compute_precision(y_true, y_pred)
        assert precision == 0.0  # Should not crash, return 0
    
    def test_recall_division_by_zero(self):
        """Test recall when no actual positives."""
        y_true = np.array([0, 0, 0, 0])
        y_pred = np.array([1, 1, 0, 0])
        
        recall = compute_recall(y_true, y_pred)
        assert recall == 0.0  # Should not crash, return 0
    
    def test_f1_zero_precision_and_recall(self):
        """Test F1 when both precision and recall are zero."""
        y_true = np.array([0, 0, 0, 0])
        y_pred = np.array([0, 0, 0, 0])
        
        f1 = compute_f1_score(y_true, y_pred)
        assert f1 == 0.0
    
    def test_auc_empty_scores(self):
        """Test AUC with empty score arrays."""
        y_true = np.array([])
        scores = np.array([])
        
        auc = compute_auc(y_true, scores)
        assert auc == 0.5  # Default for empty
    
    def test_auc_all_same_scores(self):
        """Test AUC when all scores are identical."""
        y_true = np.array([1, 0, 1, 0, 1])
        scores = np.array([0.5, 0.5, 0.5, 0.5, 0.5])
        
        auc = compute_auc(y_true, scores)
        assert auc == 0.5  # Random guessing
    
    def test_auc_perfect_separation(self):
        """Test AUC with perfect separation."""
        y_true = np.array([0, 0, 0, 1, 1, 1])
        scores = np.array([0.1, 0.2, 0.3, 0.7, 0.8, 0.9])
        
        auc = compute_auc(y_true, scores)
        assert auc == 1.0
    
    def test_auc_worst_separation(self):
        """Test AUC with worst separation."""
        y_true = np.array([0, 0, 0, 1, 1, 1])
        scores = np.array([0.9, 0.8, 0.7, 0.3, 0.2, 0.1])
        
        auc = compute_auc(y_true, scores)
        assert auc == 0.0
    
    def test_roc_curve_empty(self):
        """Test ROC curve with empty data."""
        y_true = np.array([])
        scores = np.array([])
        
        tpr, fpr = compute_roc_curve_points(y_true, scores)
        assert len(tpr) == 0
        assert len(fpr) == 0
    
    def test_roc_curve_single_point(self):
        """Test ROC curve with single sample."""
        y_true = np.array([1])
        scores = np.array([0.9])
        
        tpr, fpr = compute_roc_curve_points(y_true, scores)
        assert len(tpr) > 0
        assert len(fpr) > 0
    
    def test_pr_curve_empty(self):
        """Test PR curve with empty data."""
        y_true = np.array([])
        scores = np.array([])
        
        precision, recall = compute_pr_curve_points(y_true, scores)
        assert len(precision) == 0
        assert len(recall) == 0
    
    def test_confusion_matrix_all_correct(self):
        """Test confusion matrix with all correct predictions."""
        y_true = np.array([0, 0, 1, 1])
        y_pred = np.array([0, 0, 1, 1])
        
        cm = generate_confusion_matrix(y_true, y_pred)
        assert cm['tn'] == 2
        assert cm['fp'] == 0
        assert cm['fn'] == 0
        assert cm['tp'] == 2
    
    def test_confusion_matrix_all_wrong(self):
        """Test confusion matrix with all wrong predictions."""
        y_true = np.array([0, 0, 1, 1])
        y_pred = np.array([1, 1, 0, 0])
        
        cm = generate_confusion_matrix(y_true, y_pred)
        assert cm['tn'] == 0
        assert cm['fp'] == 2
        assert cm['fn'] == 2
        assert cm['tp'] == 0
    
    def test_confusion_matrix_imbalanced(self):
        """Test confusion matrix with imbalanced classes."""
        y_true = np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 1])
        y_pred = np.array([0, 0, 0, 0, 0, 0, 0, 0, 1, 1])
        
        cm = generate_confusion_matrix(y_true, y_pred)
        assert cm['tn'] == 8
        assert cm['fp'] == 1
        assert cm['fn'] == 0
        assert cm['tp'] == 1
    
    def test_metrics_with_float_predictions(self):
        """Test metrics with float predictions (thresholded)."""
        y_true = np.array([0, 0, 1, 1])
        scores = np.array([0.1, 0.3, 0.6, 0.9])
        
        # Threshold at 0.5
        y_pred = (scores >= 0.5).astype(int)
        metrics = compute_all_metrics(y_true, y_pred)
        
        assert metrics.precision == 1.0
        assert metrics.recall == 1.0
        assert metrics.f1_score == 1.0
    
    def test_metrics_nan_values(self):
        """Test metrics with NaN values."""
        y_true = np.array([0, 0, 1, 1])
        y_pred = np.array([0, np.nan, 1, 1])
        
        # Should handle NaN gracefully
        metrics = compute_all_metrics(y_true, y_pred)
        # NaN predictions should be treated as 0 or handled
        assert metrics.precision >= 0.0
        assert metrics.recall >= 0.0
    
    def test_metrics_extreme_imbalance(self):
        """Test metrics with extreme class imbalance."""
        y_true = np.array([0] * 999 + [1])
        y_pred = np.array([0] * 999 + [1])
        
        metrics = compute_all_metrics(y_true, y_pred)
        assert metrics.precision == 1.0
        assert metrics.recall == 1.0
        assert metrics.f1_score == 1.0
    
    def test_metrics_random_predictions_imbalanced(self):
        """Test metrics with random predictions on imbalanced data."""
        np.random.seed(42)
        y_true = np.array([0] * 999 + [1])
        y_pred = np.random.randint(0, 2, 1000)
        
        metrics = compute_all_metrics(y_true, y_pred)
        # Should not crash, values should be valid
        assert 0.0 <= metrics.precision <= 1.0
        assert 0.0 <= metrics.recall <= 1.0
        assert 0.0 <= metrics.f1_score <= 1.0
    
    def test_evaluation_metrics_dataclass(self):
        """Test EvaluationMetrics dataclass creation."""
        metrics = EvaluationMetrics(
            f1_score=0.8,
            precision=0.85,
            recall=0.75,
            auc=0.9,
            confusion_matrix={'tp': 75, 'fp': 15, 'fn': 25, 'tn': 85}
        )
        
        assert metrics.f1_score == 0.8
        assert metrics.precision == 0.85
        assert metrics.recall == 0.75
        assert metrics.auc == 0.9
    
    def test_evaluation_metrics_to_dict(self):
        """Test EvaluationMetrics to_dict method."""
        metrics = EvaluationMetrics(
            f1_score=0.8,
            precision=0.85,
            recall=0.75,
            auc=0.9,
            confusion_matrix={'tp': 75, 'fp': 15, 'fn': 25, 'tn': 85}
        )
        
        d = metrics.to_dict()
        assert 'f1_score' in d
        assert 'precision' in d
        assert 'recall' in d
        assert 'auc' in d


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
