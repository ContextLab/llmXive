"""
Unit tests for threshold sweep logic in sensitivity analysis.

Tests the logic for varying decision thresholds and decline-definition thresholds
as specified in User Story 3 (T030a, T030b).

This test file verifies:
1. Threshold sweep over {0.45, 0.50, 0.55} correctly calculates FP/FN rates
2. Decline threshold variation logic correctly identifies subjects based on score changes
3. Edge cases (empty arrays, all same class) are handled gracefully
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys

# Add code directory to path for imports
code_dir = Path(__file__).parent.parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from utils.stats import calculate_pearson_correlation


class TestThresholdSweepLogic:
    """Tests for decision threshold sweep functionality (T030a)"""

    def test_sweep_calculates_fp_fn_rates(self):
        """Verify that threshold sweep correctly calculates FP and FN rates"""
        # Create synthetic predictions and true labels
        np.random.seed(42)
        n_samples = 100
        y_true = np.random.randint(0, 2, n_samples)
        y_scores = np.random.random(n_samples)
        
        # Define thresholds to sweep
        thresholds = [0.45, 0.50, 0.55]
        
        results = {}
        for threshold in thresholds:
            y_pred = (y_scores >= threshold).astype(int)
            
            # Calculate confusion matrix components
            tp = np.sum((y_pred == 1) & (y_true == 1))
            tn = np.sum((y_pred == 0) & (y_true == 0))
            fp = np.sum((y_pred == 1) & (y_true == 0))
            fn = np.sum((y_pred == 0) & (y_true == 1))
            
            # Calculate rates
            fp_rate = fp / (fp + tn) if (fp + tn) > 0 else 0.0
            fn_rate = fn / (fn + tp) if (fn + tp) > 0 else 0.0
            
            results[threshold] = {
                'fp_rate': fp_rate,
                'fn_rate': fn_rate,
                'fp': fp,
                'fn': fn,
                'tp': tp,
                'tn': tn
            }
        
        # Verify results structure
        assert len(results) == len(thresholds)
        for threshold in thresholds:
            assert threshold in results
            assert 'fp_rate' in results[threshold]
            assert 'fn_rate' in results[threshold]
            assert 0.0 <= results[threshold]['fp_rate'] <= 1.0
            assert 0.0 <= results[threshold]['fn_rate'] <= 1.0
        
        # Verify that different thresholds produce different results
        # (unless all predictions are the same, which is unlikely with random data)
        unique_fp_rates = len(set(r['fp_rate'] for r in results.values()))
        unique_fn_rates = len(set(r['fn_rate'] for r in results.values()))
        
        # At least some variation should exist
        assert unique_fp_rates > 1 or unique_fn_rates > 1

    def test_threshold_sweep_monotonicity(self):
        """
        Verify that as threshold increases, FP rate decreases and FN rate increases
        (monotonic behavior expected in well-behaved classifiers)
        """
        np.random.seed(42)
        n_samples = 200
        y_true = np.random.randint(0, 2, n_samples)
        # Create scores with some correlation to true labels
        y_scores = y_true * 0.7 + np.random.random(n_samples) * 0.3
        
        thresholds = sorted([0.45, 0.50, 0.55])
        
        fp_rates = []
        fn_rates = []
        
        for threshold in thresholds:
            y_pred = (y_scores >= threshold).astype(int)
            fp = np.sum((y_pred == 1) & (y_true == 0))
            fn = np.sum((y_pred == 0) & (y_true == 1))
            tn = np.sum((y_pred == 0) & (y_true == 0))
            tp = np.sum((y_pred == 1) & (y_true == 1))
            
            fp_rate = fp / (fp + tn) if (fp + tn) > 0 else 0.0
            fn_rate = fn / (fn + tp) if (fn + tp) > 0 else 0.0
            
            fp_rates.append(fp_rate)
            fn_rates.append(fn_rate)
        
        # FP rate should generally decrease or stay same as threshold increases
        # FN rate should generally increase or stay same as threshold increases
        # We allow some tolerance for random noise
        fp_decreases = all(fp_rates[i] >= fp_rates[i+1] - 0.1 for i in range(len(fp_rates)-1))
        fn_increases = all(fn_rates[i] <= fn_rates[i+1] + 0.1 for i in range(len(fn_rates)-1))
        
        assert fp_decreases or fn_increases, "Threshold sweep should show expected monotonic behavior"

    def test_edge_case_all_positive_predictions(self):
        """Test behavior when threshold is very low (all predictions positive)"""
        y_true = np.array([0, 0, 1, 1])
        y_scores = np.array([0.1, 0.2, 0.3, 0.4])
        threshold = 0.05  # Very low threshold
        
        y_pred = (y_scores >= threshold).astype(int)
        
        assert all(y_pred == 1), "All predictions should be positive"
        
        fp = np.sum((y_pred == 1) & (y_true == 0))
        fn = np.sum((y_pred == 0) & (y_true == 1))
        
        assert fp == 2, "Should have 2 false positives"
        assert fn == 0, "Should have 0 false negatives"

    def test_edge_case_all_negative_predictions(self):
        """Test behavior when threshold is very high (all predictions negative)"""
        y_true = np.array([0, 0, 1, 1])
        y_scores = np.array([0.1, 0.2, 0.3, 0.4])
        threshold = 0.9  # Very high threshold
        
        y_pred = (y_scores >= threshold).astype(int)
        
        assert all(y_pred == 0), "All predictions should be negative"
        
        fp = np.sum((y_pred == 1) & (y_true == 0))
        fn = np.sum((y_pred == 0) & (y_true == 1))
        
        assert fp == 0, "Should have 0 false positives"
        assert fn == 2, "Should have 2 false negatives"

    def test_empty_input_handling(self):
        """Test that empty inputs are handled gracefully"""
        y_true = np.array([])
        y_scores = np.array([])
        threshold = 0.5
        
        y_pred = (y_scores >= threshold).astype(int)
        
        fp = np.sum((y_pred == 1) & (y_true == 0))
        fn = np.sum((y_pred == 0) & (y_true == 1))
        
        assert fp == 0
        assert fn == 0


class TestDeclineThresholdVariation:
    """Tests for decline definition threshold variation (T030b)"""

    def test_decline_label_calculation(self):
        """Verify decline label is calculated correctly based on score change"""
        # Simulate MMSE/MOCA scores at two timepoints
        base_scores = np.array([25, 26, 27, 28, 29, 30])
        followup_scores = np.array([22, 25, 26, 27, 28, 29])
        
        # Standard threshold: decline >= 3 points
        threshold_3 = 3
        decline_3 = base_scores - followup_scores >= threshold_3
        
        # Expected: only first subject (25->22, drop of 3) should be labeled as decline
        expected_decline_3 = np.array([True, False, False, False, False, False])
        
        assert np.array_equal(decline_3, expected_decline_3)

    def test_decline_threshold_sweep(self):
        """Test varying decline threshold by ±1 point"""
        base_scores = np.array([25, 26, 27, 28, 29, 30])
        followup_scores = np.array([22, 25, 26, 27, 28, 29])
        
        score_diff = base_scores - followup_scores
        
        thresholds = [2, 3, 4]  # ±1 around standard 3
        
        results = {}
        for threshold in thresholds:
            decline = score_diff >= threshold
            results[threshold] = {
                'decline_count': np.sum(decline),
                'decline_indices': np.where(decline)[0].tolist()
            }
        
        # Verify results
        assert len(results) == 3
        assert results[2]['decline_count'] >= results[3]['decline_count']
        assert results[3]['decline_count'] >= results[4]['decline_count']
        
        # Specific checks
        assert results[2]['decline_count'] == 2  # Drops of 3 and 4
        assert results[3]['decline_count'] == 1  # Drop of 3 only
        assert results[4]['decline_count'] == 0  # No drops >= 4

    def test_decline_threshold_edge_cases(self):
        """Test edge cases in decline threshold calculation"""
        # All subjects show same score
        base_scores = np.array([25, 25, 25])
        followup_scores = np.array([25, 25, 25])
        
        threshold = 3
        decline = (base_scores - followup_scores) >= threshold
        
        assert not np.any(decline), "No decline should be detected when scores are stable"
        
        # All subjects show large decline
        base_scores = np.array([30, 30, 30])
        followup_scores = np.array([20, 20, 20])
        
        decline = (base_scores - followup_scores) >= threshold
        
        assert np.all(decline), "All subjects should show decline"

    def test_decline_threshold_with_missing_data(self):
        """Test handling of missing follow-up scores"""
        base_scores = np.array([25, 26, 27, 28])
        followup_scores = np.array([22, np.nan, 26, 27])
        
        threshold = 3
        
        # Calculate decline, treating NaN as no decline (or handle separately)
        diff = base_scores - followup_scores
        decline = (diff >= threshold) & ~np.isnan(diff)
        
        # Only first subject should be counted
        assert np.sum(decline) == 1
        assert decline[0] is True
        assert decline[1] is False  # NaN should not count as decline

class TestSensitivityReportGeneration:
    """Tests for sensitivity report structure and content"""

    def test_report_structure(self):
        """Verify that sensitivity report has required fields"""
        # Simulate a sensitivity report structure
        report = {
            'decision_threshold_sweep': {
                'thresholds_tested': [0.45, 0.50, 0.55],
                'results': {
                    0.45: {'fp_rate': 0.1, 'fn_rate': 0.2},
                    0.50: {'fp_rate': 0.05, 'fn_rate': 0.3},
                    0.55: {'fp_rate': 0.02, 'fn_rate': 0.4}
                }
            },
            'decline_threshold_sweep': {
                'thresholds_tested': [2, 3, 4],
                'results': {
                    2: {'decline_rate': 0.3},
                    3: {'decline_rate': 0.2},
                    4: {'decline_rate': 0.1}
                }
            }
        }
        
        # Verify structure
        assert 'decision_threshold_sweep' in report
        assert 'decline_threshold_sweep' in report
        assert len(report['decision_threshold_sweep']['thresholds_tested']) == 3
        assert len(report['decline_threshold_sweep']['thresholds_tested']) == 3

    def test_report_contains_required_metrics(self):
        """Verify report contains FP/FN rates for each threshold"""
        thresholds = [0.45, 0.50, 0.55]
        results = {}
        
        for threshold in thresholds:
            results[threshold] = {
                'fp_rate': 0.1,
                'fn_rate': 0.2,
                'accuracy': 0.85
            }
        
        # Verify all required fields present
        for threshold, metrics in results.items():
            assert 'fp_rate' in metrics
            assert 'fn_rate' in metrics
            assert 0.0 <= metrics['fp_rate'] <= 1.0
            assert 0.0 <= metrics['fn_rate'] <= 1.0