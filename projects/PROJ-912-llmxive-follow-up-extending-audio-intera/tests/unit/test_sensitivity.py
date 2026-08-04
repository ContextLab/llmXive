"""
Unit test for sensitivity sweep in code/analysis/sensitivity.py.

This test verifies that the sensitivity analysis logic correctly:
1. Sweeps through specified thresholds (0.01, 0.05, 0.1).
2. Calculates False Positive Rate (FPR) and False Negative Rate (FNR) for each.
3. Identifies the optimal threshold based on a defined metric (e.g., F1 score or balanced accuracy).
4. Handles edge cases (e.g., no positives, no negatives).

Prerequisites:
- code/analysis/sensitivity.py must be implemented with a function `run_sensitivity_analysis`.
- The function must accept logits and ground truth labels.
"""

import pytest
import numpy as np
import sys
import os

# Ensure the code directory is in the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from analysis.sensitivity import run_sensitivity_analysis

class TestSensitivitySweep:
    """Test cases for the sensitivity sweep functionality."""

    def test_sweep_thresholds_basic(self):
        """Test that the function sweeps through the expected thresholds."""
        # Generate synthetic but deterministic data for testing
        # 100 samples: 50 positive, 50 negative
        np.random.seed(42)
        num_pos = 50
        num_neg = 50
        
        # Simulate logits: positives tend to be higher, negatives lower
        pos_logits = np.random.normal(loc=2.0, scale=0.5, size=num_pos)
        neg_logits = np.random.normal(loc=-2.0, scale=0.5, size=num_neg)
        
        logits = np.concatenate([pos_logits, neg_logits])
        labels = np.concatenate([np.ones(num_pos), np.zeros(num_neg)])
        
        thresholds = [0.01, 0.05, 0.1]
        
        results = run_sensitivity_analysis(logits, labels, thresholds)
        
        assert len(results) == len(thresholds), "Should return results for all thresholds"
        
        for i, res in enumerate(results):
            assert res['threshold'] == thresholds[i], f"Threshold mismatch at index {i}"
            assert 'fpr' in res, "Result missing 'fpr'"
            assert 'fnr' in res, "Result missing 'fnr'"
            assert 'f1_score' in res, "Result missing 'f1_score'"

    def test_fpr_fnr_calculation(self):
        """Verify FPR and FNR calculations are mathematically correct."""
        # Construct a scenario with known outcomes
        # True Positives (TP), False Positives (FP), True Negatives (TN), False Negatives (FN)
        # Let's create a case where:
        # At threshold 0.5:
        #  - All positives > 0.5 (TP = 10, FN = 0)
        #  - Half negatives > 0.5 (FP = 5, TN = 5)
        # Total Positives = 10, Total Negatives = 10
        
        num_pos = 10
        num_neg = 10
        
        # Positives: all high
        pos_logits = np.ones(num_pos) * 0.8
        # Negatives: half high, half low
        neg_logits = np.concatenate([np.ones(5) * 0.8, np.ones(5) * 0.2])
        
        logits = np.concatenate([pos_logits, neg_logits])
        labels = np.concatenate([np.ones(num_pos), np.zeros(num_neg)])
        
        # We test at threshold 0.5
        thresholds = [0.5]
        
        results = run_sensitivity_analysis(logits, labels, thresholds)
        res = results[0]
        
        # Expected:
        # TP = 10, FN = 0 -> Recall = 1.0
        # FP = 5, TN = 5 -> Specificity = 0.5
        # FPR = FP / (FP + TN) = 5 / 10 = 0.5
        # FNR = FN / (FN + TP) = 0 / 10 = 0.0
        
        expected_fpr = 0.5
        expected_fnr = 0.0
        
        assert np.isclose(res['fpr'], expected_fpr), f"FPR mismatch: {res['fpr']} vs {expected_fpr}"
        assert np.isclose(res['fnr'], expected_fnr), f"FNR mismatch: {res['fnr']} vs {expected_fnr}"

    def test_edge_case_no_positives(self):
        """Test behavior when there are no positive samples."""
        logits = np.array([0.1, 0.2, 0.3])
        labels = np.array([0, 0, 0])
        
        thresholds = [0.5]
        
        # Should not raise an exception, but handle division by zero gracefully
        # FPR = FP / (FP + TN). If no positives, FN=0, TP=0.
        # If threshold separates some negatives as positive: FP > 0, TN >= 0.
        # FNR = FN / (FN + TP) -> 0/0 -> usually defined as 0 or NaN.
        
        results = run_sensitivity_analysis(logits, labels, thresholds)
        
        # Check that the function returned a result without crashing
        assert len(results) == 1
        # FNR should be 0.0 or handled gracefully (e.g., 0.0 if defined as such)
        # FPR should be calculated correctly based on negatives
        assert 'fpr' in results[0]
        assert 'fnr' in results[0]

    def test_edge_case_no_negatives(self):
        """Test behavior when there are no negative samples."""
        logits = np.array([0.6, 0.7, 0.8])
        labels = np.array([1, 1, 1])
        
        thresholds = [0.5]
        
        results = run_sensitivity_analysis(logits, labels, thresholds)
        
        assert len(results) == 1
        # FPR = FP / (FP + TN). If no negatives, FP=0, TN=0 -> 0/0 -> 0.0
        # FNR = FN / (FN + TP). If all positive and threshold low: FN=0, TP=3 -> 0.0
        assert 'fpr' in results[0]
        assert 'fnr' in results[0]

    def test_optimal_threshold_selection(self):
        """Test that the function identifies the best threshold if requested."""
        # Create data where one threshold is clearly better
        # Positives: 10 samples at 0.9
        # Negatives: 10 samples at 0.1
        # Threshold 0.5 should give perfect classification (FPR=0, FNR=0)
        # Threshold 0.01 or 0.99 should be worse.
        
        pos_logits = np.ones(10) * 0.9
        neg_logits = np.ones(10) * 0.1
        
        logits = np.concatenate([pos_logits, neg_logits])
        labels = np.concatenate([np.ones(10), np.zeros(10)])
        
        thresholds = [0.01, 0.5, 0.99]
        
        results = run_sensitivity_analysis(logits, labels, thresholds)
        
        # Find the result with the highest F1 score (or lowest sum of FPR+FNR)
        best_result = max(results, key=lambda x: x.get('f1_score', 0))
        
        assert best_result['threshold'] == 0.5, "Optimal threshold should be 0.5"
        assert np.isclose(best_result['fpr'], 0.0), "FPR should be 0 at optimal threshold"
        assert np.isclose(best_result['fnr'], 0.0), "FNR should be 0 at optimal threshold"

    def test_default_thresholds_used_when_empty(self):
        """Test that default thresholds are used if the input list is empty."""
        logits = np.array([0.5, 0.6, 0.4, 0.3])
        labels = np.array([1, 1, 0, 0])
        
        thresholds = []
        
        results = run_sensitivity_analysis(logits, labels, thresholds)
        
        # Should use default thresholds [0.01, 0.05, 0.1]
        assert len(results) == 3
        expected_thresholds = [0.01, 0.05, 0.1]
        for i, res in enumerate(results):
            assert res['threshold'] == expected_thresholds[i]

if __name__ == '__main__':
    pytest.main([__file__, '-v'])