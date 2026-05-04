"""
Contract test for evaluation metrics schema.

Validates that evaluation outputs conform to specs/contracts/evaluation_metrics.schema.yaml
"""
import pytest
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np
from datetime import datetime

# Project root for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
import sys
sys.path.insert(0, str(PROJECT_ROOT / "code"))

# Import from evaluation module
from src.evaluation.metrics import (
    EvaluationMetrics,
    compute_f1_score,
    compute_precision,
    compute_recall,
    compute_auc,
    generate_confusion_matrix
)
from src.evaluation.plots import (
    generate_roc_curve,
    generate_pr_curve
)

class TestEvaluationMetricsSchema:
    """Validate evaluation metrics outputs match schema."""

    def test_evaluation_metrics_schema(self):
        """EvaluationMetrics must have required fields with correct types."""
        metrics = EvaluationMetrics(
            f1_score=0.85,
            precision=0.90,
            recall=0.80,
            auc_roc=0.92,
            auc_pr=0.88,
            accuracy=0.95,
            confusion_matrix=np.array([[90, 5], [3, 2]]),
            threshold=0.5,
            timestamp=datetime.now(),
            dataset_name="test_dataset"
        )
        
        # Validate required fields exist
        assert hasattr(metrics, 'f1_score')
        assert hasattr(metrics, 'precision')
        assert hasattr(metrics, 'recall')
        assert hasattr(metrics, 'auc_roc')
        assert hasattr(metrics, 'auc_pr')
        assert hasattr(metrics, 'accuracy')
        assert hasattr(metrics, 'confusion_matrix')
        assert hasattr(metrics, 'threshold')
        assert hasattr(metrics, 'timestamp')
        assert hasattr(metrics, 'dataset_name')
        
        # Validate field types and ranges
        assert isinstance(metrics.f1_score, (int, float, np.number))
        assert 0 <= metrics.f1_score <= 1
        assert isinstance(metrics.precision, (int, float, np.number))
        assert 0 <= metrics.precision <= 1
        assert isinstance(metrics.recall, (int, float, np.number))
        assert 0 <= metrics.recall <= 1
        assert isinstance(metrics.auc_roc, (int, float, np.number))
        assert 0 <= metrics.auc_roc <= 1
        assert isinstance(metrics.auc_pr, (int, float, np.number))
        assert 0 <= metrics.auc_pr <= 1
        assert isinstance(metrics.confusion_matrix, np.ndarray)
        assert metrics.confusion_matrix.shape == (2, 2)

    def test_metric_computation_functions(self):
        """Metric computation functions must return valid values."""
        # Create test data
        y_true = np.array([0, 0, 0, 0, 1, 1, 1, 1])
        y_pred = np.array([0, 0, 0, 1, 0, 1, 1, 1])
        scores = np.array([0.1, 0.2, 0.3, 0.4, 0.6, 0.7, 0.8, 0.9])
        
        # Test F1 score computation
        f1 = compute_f1_score(y_true, y_pred)
        assert isinstance(f1, (int, float, np.number))
        assert 0 <= f1 <= 1
        
        # Test precision computation
        precision = compute_precision(y_true, y_pred)
        assert isinstance(precision, (int, float, np.number))
        assert 0 <= precision <= 1
        
        # Test recall computation
        recall = compute_recall(y_true, y_pred)
        assert isinstance(recall, (int, float, np.number))
        assert 0 <= recall <= 1
        
        # Test AUC computation
        auc = compute_auc(y_true, scores)
        assert isinstance(auc, (int, float, np.number))
        assert 0 <= auc <= 1

    def test_confusion_matrix_structure(self):
        """Confusion matrix must have valid 2x2 structure."""
        y_true = np.array([0, 0, 0, 0, 1, 1, 1, 1])
        y_pred = np.array([0, 0, 0, 1, 0, 1, 1, 1])
        
        cm = generate_confusion_matrix(y_true, y_pred)
        
        assert cm.shape == (2, 2)
        assert cm.dtype in [np.int64, np.int32, int]
        assert np.all(cm >= 0)
        
        # Verify sum equals total samples
        assert np.sum(cm) == len(y_true)

    def test_roc_pr_curve_generation(self, tmp_path):
        """ROC and PR curve generators must produce valid outputs."""
        y_true = np.array([0, 0, 0, 0, 1, 1, 1, 1])
        scores = np.array([0.1, 0.2, 0.3, 0.4, 0.6, 0.7, 0.8, 0.9])
        
        # Test ROC curve
        roc_result = generate_roc_curve(y_true, scores)
        assert 'fpr' in roc_result
        assert 'tpr' in roc_result
        assert 'auc' in roc_result
        assert len(roc_result['fpr']) == len(roc_result['tpr'])
        
        # Test PR curve
        pr_result = generate_pr_curve(y_true, scores)
        assert 'precision' in pr_result
        assert 'recall' in pr_result
        assert 'auc' in pr_result
        assert len(pr_result['precision']) == len(pr_result['recall'])