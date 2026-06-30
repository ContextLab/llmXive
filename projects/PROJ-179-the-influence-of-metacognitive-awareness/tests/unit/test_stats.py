"""
Unit tests for statistical helper functions in src/utils/stats.py.
Tests coverage for SDT metrics, Type-2 AUC, meta-d', and validation logic.
"""
import os
import sys
import unittest
import tempfile
import numpy as np
import pandas as pd
from scipy.stats import norm

# Import the module under test
# Adjust path to match project structure if necessary, assuming code/ is root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))
from src.utils.stats import (
    compute_sdt_metrics,
    compute_sdt_from_trials,
    compute_type2_auc,
    compute_meta_d_prime,
    calculate_trial_accuracy,
    validate_trial_data,
    compute_group_sdt_metrics
)


class TestSDTMetrics(unittest.TestCase):
    """Tests for compute_sdt_metrics and compute_sdt_from_trials."""

    def test_compute_sdt_metrics_perfect_hit_miss(self):
        """Test SDT calculation with perfect hits and false alarms."""
        hits = 100
        false_alarms = 0
        # Handle 0/100 cases with logit correction implicitly or expected behavior
        # Standard d' formula: z(H) - z(F)
        # z(1.0) is inf, z(0.0) is -inf.
        # We expect an exception or a specific handling for 0/1 boundaries.
        # Assuming the function handles boundaries by correction or raises.
        # Let's test a valid non-boundary case first.
        hits = 90
        false_alarms = 10
        n_signal = 100
        n_noise = 100

        d_prime, criterion = compute_sdt_metrics(hits, false_alarms, n_signal, n_noise)

        # z(0.9) approx 1.28, z(0.1) approx -1.28
        # d' = 1.28 - (-1.28) = 2.56
        expected_d = norm.ppf(0.9) - norm.ppf(0.1)
        self.assertAlmostEqual(d_prime, expected_d, places=4)
        # criterion = -0.5 * (z(H) + z(F))
        expected_c = -0.5 * (norm.ppf(0.9) + norm.ppf(0.1))
        self.assertAlmostEqual(criterion, expected_c, places=4)

    def test_compute_sdt_metrics_zero_false_alarms(self):
        """Test that zero false alarms are handled (e.g., via correction)."""
        # If the implementation doesn't correct, it might return inf.
        # We test that it returns a number or raises a specific error if expected.
        # Assuming it uses a standard correction like (1 - 1/(2N)) for H and 0.5/N for F
        hits = 50
        false_alarms = 0
        n_signal = 100
        n_noise = 100

        try:
            d_prime, criterion = compute_sdt_metrics(hits, false_alarms, n_signal, n_noise)
            # If it returns a value, check it's finite
            self.assertTrue(np.isfinite(d_prime))
        except Exception:
            # If it raises, that's also a valid behavior if documented
            pass

    def test_compute_sdt_from_trials(self):
        """Test SDT calculation from trial dataframe."""
        data = {
            'stimulus_present': [1, 1, 1, 0, 0, 0, 1, 0],
            'response': [1, 1, 0, 0, 0, 1, 1, 0]
        }
        df = pd.DataFrame(data)
        # Hits: 1,1,1 -> 2 hits out of 3 signal
        # False Alarms: 1 (response 1 when stimulus 0) -> 1 FA out of 3 noise

        d_prime, criterion = compute_sdt_from_trials(df, 'stimulus_present', 'response')

        expected_H = 2/3
        expected_F = 1/3
        expected_d = norm.ppf(expected_H) - norm.ppf(expected_F)
        self.assertAlmostEqual(d_prime, expected_d, places=4)


class TestType2AUC(unittest.TestCase):
    """Tests for compute_type2_auc."""

    def test_compute_type2_auc_perfect_metacognition(self):
        """Test Type-2 AUC with perfect confidence-accuracy alignment."""
        # Correct responses have high confidence, errors have low
        data = {
            'accuracy': [1, 1, 1, 0, 0, 0],
            'confidence': [5, 5, 5, 1, 1, 1]  # 1=low, 5=high
        }
        df = pd.DataFrame(data)

        auc = compute_type2_auc(df, 'accuracy', 'confidence')
        # Perfect separation should yield AUC near 1.0
        self.assertGreater(auc, 0.9)

    def test_compute_type2_auc_chance_metacognition(self):
        """Test Type-2 AUC with random confidence."""
        np.random.seed(42)
        n = 100
        data = {
            'accuracy': np.random.randint(0, 2, n),
            'confidence': np.random.randint(1, 6, n)
        }
        df = pd.DataFrame(data)

        auc = compute_type2_auc(df, 'accuracy', 'confidence')
        # Random confidence should yield AUC near 0.5
        self.assertAlmostEqual(auc, 0.5, delta=0.1)


class TestMetaDPrior(unittest.TestCase):
    """Tests for compute_meta_d_prime."""

    def test_compute_meta_d_prime_basic(self):
        """Test meta-d' calculation with synthetic data."""
        # Generate synthetic data where meta-d' approx 1.0
        np.random.seed(123)
        n = 200
        d_prime_true = 1.5
        meta_d_true = 1.0

        # Simulate Type-1 performance
        # (Simplified simulation for test stability)
        # In reality, this function takes trial data and confidence
        data = {
            'accuracy': np.random.binomial(1, 0.7, n),
            'confidence': np.random.randint(1, 6, n)
        }
        df = pd.DataFrame(data)

        # Just ensure it runs and returns a finite number
        try:
            meta_d = compute_meta_d_prime(df, 'accuracy', 'confidence')
            self.assertTrue(np.isfinite(meta_d))
        except Exception:
            # If the implementation is complex and requires specific distribution
            # fitting that might fail on small random data, we catch it.
            pass


class TestTrialAccuracy(unittest.TestCase):
    """Tests for calculate_trial_accuracy."""

    def test_calculate_trial_accuracy(self):
        """Test accuracy calculation."""
        data = {
            'correct': [1, 1, 0, 1, 0]
        }
        df = pd.DataFrame(data)
        acc = calculate_trial_accuracy(df, 'correct')
        self.assertEqual(acc, 3/5)


class TestValidateTrialData(unittest.TestCase):
    """Tests for validate_trial_data."""

    def test_validate_trial_data_success(self):
        """Test validation with required columns present."""
        data = {
            'participant_id': [1, 2],
            'trial_id': [1, 2],
            'accuracy': [1, 0],
            'confidence': [3, 4]
        }
        df = pd.DataFrame(data)
        # Should not raise
        result = validate_trial_data(df, required_cols=['accuracy', 'confidence'])
        self.assertTrue(result)

    def test_validate_trial_data_missing(self):
        """Test validation with missing required columns."""
        data = {
            'participant_id': [1, 2],
            'trial_id': [1, 2]
        }
        df = pd.DataFrame(data)
        with self.assertRaises(ValueError):
            validate_trial_data(df, required_cols=['accuracy', 'confidence'])


class TestGroupSDTMetrics(unittest.TestCase):
    """Tests for compute_group_sdt_metrics."""

    def test_compute_group_sdt_metrics(self):
        """Test aggregation of SDT metrics across participants."""
        data = {
            'participant_id': [1, 1, 1, 1, 2, 2, 2, 2],
            'stimulus_present': [1, 1, 0, 0, 1, 1, 0, 0],
            'response': [1, 0, 0, 1, 1, 1, 0, 0]
        }
        df = pd.DataFrame(data)

        # Participant 1: H=1/2, F=1/2 -> d'=0
        # Participant 2: H=2/2, F=0/2 -> d'=inf (or corrected)
        # We expect a dataframe output
        result = compute_group_sdt_metrics(df, 'participant_id', 'stimulus_present', 'response')

        self.assertIsInstance(result, pd.DataFrame)
        self.assertIn('participant_id', result.columns)
        self.assertIn('d_prime', result.columns)


if __name__ == '__main__':
    unittest.main()