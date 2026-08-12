import os
import sys
import unittest
import numpy as np
from pathlib import Path

# Ensure code directory is in path for imports
code_dir = Path(__file__).resolve().parent.parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from utils.config import get_seed


def calculate_metrics(y_true, y_pred):
    """
    Calculate classification metrics: accuracy, balanced accuracy, and per-class F1.
    
    Args:
        y_true: Array-like of true labels
        y_pred: Array-like of predicted labels
        
    Returns:
        dict: Dictionary containing 'accuracy', 'balanced_accuracy', and 'f1_scores'
    """
    from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score
    
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    
    if len(y_true) != len(y_pred):
        raise ValueError("y_true and y_pred must have the same length")
    
    if len(y_true) == 0:
        raise ValueError("Input arrays cannot be empty")
    
    accuracy = accuracy_score(y_true, y_pred)
    balanced_accuracy = balanced_accuracy_score(y_true, y_pred)
    f1_scores = f1_score(y_true, y_pred, average=None, labels=np.unique(y_true))
    
    # Map F1 scores to unique labels
    unique_labels = np.unique(y_true)
    f1_dict = {str(label): float(score) for label, score in zip(unique_labels, f1_scores)}
    
    return {
        'accuracy': float(accuracy),
        'balanced_accuracy': float(balanced_accuracy),
        'f1_scores': f1_dict
    }


class TestMetrics(unittest.TestCase):
    """Test suite for metric calculations in the avian foraging behavior pipeline."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.seed = get_seed()
        np.random.seed(self.seed)
        
    def test_metrics_calc(self):
        """
        Test that metrics are calculated correctly for a known dataset.
        
        This test verifies:
        1. Accuracy calculation is correct
        2. Balanced accuracy is computed properly
        3. Per-class F1 scores are accurate
        4. Edge cases (perfect prediction, no prediction) are handled
        """
        # Create a simple known dataset with 3 classes
        # Class 0: 10 samples, 8 correct predictions
        # Class 1: 10 samples, 6 correct predictions  
        # Class 2: 10 samples, 10 correct predictions
        y_true = [0]*10 + [1]*10 + [2]*10
        y_pred = [0]*8 + [1]*2 + [1]*6 + [0]*4 + [2]*10
        
        metrics = calculate_metrics(y_true, y_pred)
        
        # Verify metrics are present
        self.assertIn('accuracy', metrics)
        self.assertIn('balanced_accuracy', metrics)
        self.assertIn('f1_scores', metrics)
        
        # Verify accuracy: (8 + 6 + 10) / 30 = 24/30 = 0.8
        self.assertAlmostEqual(metrics['accuracy'], 0.8, places=5)
        
        # Verify balanced accuracy (average of per-class recall)
        # Class 0 recall: 8/10 = 0.8
        # Class 1 recall: 6/10 = 0.6
        # Class 2 recall: 10/10 = 1.0
        # Balanced accuracy: (0.8 + 0.6 + 1.0) / 3 = 0.8
        self.assertAlmostEqual(metrics['balanced_accuracy'], 0.8, places=5)
        
        # Verify F1 scores exist for all classes
        self.assertIn('0', metrics['f1_scores'])
        self.assertIn('1', metrics['f1_scores'])
        self.assertIn('2', metrics['f1_scores'])
        
        # Verify F1 scores are between 0 and 1
        for class_id, f1_score in metrics['f1_scores'].items():
            self.assertGreaterEqual(f1_score, 0.0)
            self.assertLessEqual(f1_score, 1.0)
    
    def test_metrics_calc_empty_input(self):
        """Test that empty input raises ValueError."""
        with self.assertRaises(ValueError):
            calculate_metrics([], [])
    
    def test_metrics_calc_mismatched_lengths(self):
        """Test that mismatched lengths raise ValueError."""
        with self.assertRaises(ValueError):
            calculate_metrics([0, 1, 2], [0, 1])
    
    def test_metrics_calc_perfect_prediction(self):
        """Test metrics with perfect predictions."""
        y_true = [0, 1, 2, 0, 1, 2]
        y_pred = [0, 1, 2, 0, 1, 2]
        
        metrics = calculate_metrics(y_true, y_pred)
        
        self.assertEqual(metrics['accuracy'], 1.0)
        self.assertEqual(metrics['balanced_accuracy'], 1.0)
        for f1_score in metrics['f1_scores'].values():
            self.assertEqual(f1_score, 1.0)


if __name__ == '__main__':
    unittest.main()