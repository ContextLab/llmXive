import os
import sys
import unittest
import numpy as np
from pathlib import Path

# Import from project utils to ensure consistency
from utils.config import get_seed, get_project_root

def calculate_metrics(y_true, y_pred):
    """
    Calculate basic classification metrics.
    
    Args:
        y_true: Array-like of true labels
        y_pred: Array-like of predicted labels
        
    Returns:
        dict: Dictionary containing accuracy, precision, recall, f1_score
    """
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    
    if len(y_true) != len(y_pred):
        raise ValueError("y_true and y_pred must have the same length")
    
    # Calculate accuracy
    accuracy = np.mean(y_true == y_pred)
    
    # Calculate per-class metrics (assuming binary or multiclass)
    unique_labels = np.unique(np.concatenate([y_true, y_pred]))
    
    metrics = {
        'accuracy': accuracy,
        'per_class': {}
    }
    
    for label in unique_labels:
        tp = np.sum((y_true == label) & (y_pred == label))
        fp = np.sum((y_true != label) & (y_pred == label))
        fn = np.sum((y_true == label) & (y_pred != label))
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        
        metrics['per_class'][str(label)] = {
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'support': np.sum(y_true == label)
        }
    
    return metrics


class TestMetrics(unittest.TestCase):
    """Test suite for metric calculations."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.seed = get_seed()
        np.random.seed(self.seed)
        
    def test_metrics_calc(self):
        """
        Test metric calculation with known values.
        
        This test currently asserts False to ensure the test fails initially,
        verifying that pytest returns exit code 1 before implementation.
        Once metrics are implemented, this should be replaced with actual
        assertions against known values.
        """
        # Create simple test data
        y_true = np.array([0, 1, 1, 0, 1, 0, 1, 1])
        y_pred = np.array([0, 1, 0, 0, 1, 1, 1, 1])
        
        # Calculate metrics
        metrics = calculate_metrics(y_true, y_pred)
        
        # TODO: Replace with actual assertions after implementation
        # For now, assert False to ensure test fails initially
        self.assertFalse(True, "This test is a stub - replace with actual assertions")
        
        # Example of what the final test should look like:
        # self.assertAlmostEqual(metrics['accuracy'], 0.75, places=2)
        # self.assertIn('0', metrics['per_class'])
        # self.assertIn('1', metrics['per_class'])
        
    def test_metrics_length_mismatch(self):
        """Test that mismatched lengths raise an error."""
        y_true = np.array([0, 1, 1])
        y_pred = np.array([0, 1])
        
        with self.assertRaises(ValueError):
            calculate_metrics(y_true, y_pred)
            
    def test_metrics_perfect_prediction(self):
        """Test perfect prediction yields 1.0 accuracy."""
        y_true = np.array([0, 1, 1, 0, 1])
        y_pred = np.array([0, 1, 1, 0, 1])
        
        metrics = calculate_metrics(y_true, y_pred)
        self.assertEqual(metrics['accuracy'], 1.0)
        
    def test_metrics_class_existence(self):
        """Test that per-class metrics exist for all unique labels."""
        y_true = np.array([0, 1, 2, 0, 1, 2])
        y_pred = np.array([0, 1, 2, 0, 1, 2])
        
        metrics = calculate_metrics(y_true, y_pred)
        unique_labels = set(map(str, np.unique(np.concatenate([y_true, y_pred]))))
        metric_labels = set(metrics['per_class'].keys())
        
        self.assertEqual(unique_labels, metric_labels)


if __name__ == '__main__':
    unittest.main()