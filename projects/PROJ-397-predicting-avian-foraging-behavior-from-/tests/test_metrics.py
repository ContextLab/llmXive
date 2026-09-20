import os
import sys
import unittest
import numpy as np
from pathlib import Path
from utils.config import get_models_dir

# Add the code directory to the path to allow imports from sibling modules
code_root = Path(__file__).resolve().parent.parent
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from sklearn.metrics import balanced_accuracy_score, f1_score

def calculate_metrics(y_true, y_pred):
    """
    Calculate balanced accuracy and F1 scores.
    
    Args:
        y_true: Array-like of true labels
        y_pred: Array-like of predicted labels
        
    Returns:
        dict: Dictionary containing balanced_accuracy and f1_score
    """
    bal_acc = balanced_accuracy_score(y_true, y_pred)
    f1 = f1_score(y_true, y_pred, average='weighted')
    return {
        'balanced_accuracy': bal_acc,
        'f1_score': f1
    }

class TestMetrics(unittest.TestCase):
    """Unit tests for balanced accuracy and F1 calculations."""

    def test_balanced_accuracy_perfect(self):
        """Test balanced accuracy with perfect predictions."""
        y_true = [0, 1, 2, 0, 1, 2]
        y_pred = [0, 1, 2, 0, 1, 2]
        
        result = calculate_metrics(y_true, y_pred)
        
        # Perfect prediction should yield 1.0 balanced accuracy
        self.assertAlmostEqual(result['balanced_accuracy'], 1.0, places=5)

    def test_f1_perfect(self):
        """Test F1 score with perfect predictions."""
        y_true = [0, 1, 2, 0, 1, 2]
        y_pred = [0, 1, 2, 0, 1, 2]
        
        result = calculate_metrics(y_true, y_pred)
        
        # Perfect prediction should yield 1.0 F1
        self.assertAlmostEqual(result['f1_score'], 1.0, places=5)

    def test_balanced_accuracy_random(self):
        """Test balanced accuracy with random predictions (known outcome)."""
        # Construct a specific case where we know the outcome
        # Class 0: 2 samples, predicted 1 correctly
        # Class 1: 2 samples, predicted 1 correctly
        # Class 2: 2 samples, predicted 1 correctly
        # Recall per class = 0.5, Balanced Accuracy = 0.5
        y_true = [0, 0, 1, 1, 2, 2]
        y_pred = [0, 1, 1, 0, 2, 0] 
        
        result = calculate_metrics(y_true, y_pred)
        
        # Manually verify:
        # Class 0: TP=1, FN=1 -> Recall=0.5
        # Class 1: TP=1, FN=1 -> Recall=0.5
        # Class 2: TP=1, FN=1 -> Recall=0.5
        # Balanced Accuracy = mean(0.5, 0.5, 0.5) = 0.5
        self.assertAlmostEqual(result['balanced_accuracy'], 0.5, places=5)

    def test_f1_imbalanced_classes(self):
        """Test F1 score with imbalanced classes."""
        # 5 samples of class 0, 2 samples of class 1
        # Predictions: 4 correct for class 0, 1 correct for class 1
        y_true = [0, 0, 0, 0, 0, 1, 1]
        y_pred = [0, 0, 0, 0, 1, 1, 0]
        
        result = calculate_metrics(y_true, y_pred)
        
        # Precision Class 0: 4/5 = 0.8, Recall Class 0: 4/5 = 0.8 -> F1 = 0.8
        # Precision Class 1: 1/2 = 0.5, Recall Class 1: 1/2 = 0.5 -> F1 = 0.5
        # Weighted F1 = (5/7)*0.8 + (2/7)*0.5 = 4/7 + 1/7 = 5/7 approx 0.714
        expected_f1 = (5/7)*0.8 + (2/7)*0.5
        self.assertAlmostEqual(result['f1_score'], expected_f1, places=5)

    def test_empty_arrays(self):
        """Test that empty arrays raise an error or handle gracefully."""
        # sklearn raises ValueError for empty arrays
        with self.assertRaises(ValueError):
            calculate_metrics([], [])

    def test_single_class(self):
        """Test metrics when only one class is present."""
        y_true = [0, 0, 0]
        y_pred = [0, 0, 0]
        
        result = calculate_metrics(y_true, y_pred)
        
        self.assertAlmostEqual(result['balanced_accuracy'], 1.0, places=5)
        self.assertAlmostEqual(result['f1_score'], 1.0, places=5)

if __name__ == '__main__':
    unittest.main()