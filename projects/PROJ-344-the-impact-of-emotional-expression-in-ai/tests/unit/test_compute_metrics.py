"""
tests/unit/test_compute_metrics.py

Unit tests for the intra-modal consistency metric calculation.
"""

import unittest
import numpy as np
import pandas as pd
import sys
import os

# Add parent directory to path for imports if running from tests/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from code.compute_metrics import (
    compute_max_abs_cross_correlation,
    compute_consistency_score,
    process_interaction_features,
    validate_feature_input
)

class TestCrossCorrelation(unittest.TestCase):
    
    def test_perfect_correlation_zero_lag(self):
        """Test with identical signals -> correlation should be 1.0"""
        signal = np.linspace(0, 10, 100)
        corr = compute_max_abs_cross_correlation(signal, signal, 10)
        self.assertAlmostEqual(corr, 1.0, places=4)
    
    def test_perfect_negative_correlation(self):
        """Test with inverted signals -> correlation should be 1.0 (abs)"""
        signal_a = np.linspace(0, 10, 100)
        signal_b = -signal_a
        corr = compute_max_abs_cross_correlation(signal_a, signal_b, 10)
        self.assertAlmostEqual(corr, 1.0, places=4)
    
    def test_lag_detection(self):
        """Test that lag is detected correctly within window"""
        signal_a = np.sin(np.linspace(0, 10*np.pi, 200))
        signal_b = np.sin(np.linspace(0, 10*np.pi, 200) + np.pi/2) # 90 degree shift
        
        # With sufficient lag window, we should find high correlation
        # The exact value depends on the shift and window size
        corr = compute_max_abs_cross_correlation(signal_a, signal_b, 50)
        self.assertGreater(corr, 0.5)
    
    def test_short_signals(self):
        """Test with signals too short for correlation"""
        signal_a = np.array([1.0])
        signal_b = np.array([1.0])
        corr = compute_max_abs_cross_correlation(signal_a, signal_b, 5)
        self.assertEqual(corr, 0.0)
    
    def test_zero_variance(self):
        """Test with constant signals (zero variance)"""
        signal_a = np.ones(100)
        signal_b = np.ones(100)
        corr = compute_max_abs_cross_correlation(signal_a, signal_b, 10)
        self.assertEqual(corr, 0.0)

class TestConsistencyScore(unittest.TestCase):
    
    def test_score_range(self):
        """Test that consistency score is always in [0, 1]"""
        signal_a = np.random.randn(100)
        signal_b = np.random.randn(100)
        
        score = compute_consistency_score(signal_a, signal_b, 100, 2.0)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)

class TestProcessInteractionFeatures(unittest.TestCase):
    
    def setUp(self):
        self.df = pd.DataFrame({
            'interaction_id': ['int-1', 'int-1', 'int-2'],
            'timestamp': [1.0, 2.0, 1.0],
            'facial_valence': [0.5, 0.6, 0.1],
            'vocal_energy': [0.4, 0.5, 0.2]
        })
    
    def test_valid_interaction(self):
        result = process_interaction_features(self.df, 'int-1')
        self.assertIsNotNone(result)
        self.assertEqual(result['interaction_id'], 'int-1')
        self.assertIn('consistency_score', result)
    
    def test_missing_interaction(self):
        result = process_interaction_features(self.df, 'int-999')
        self.assertIsNone(result)
    
    def test_invalid_columns(self):
        bad_df = pd.DataFrame({
            'interaction_id': ['int-1'],
            'timestamp': [1.0]
        })
        result = process_interaction_features(bad_df, 'int-1')
        self.assertIsNone(result)

class TestValidateFeatureInput(unittest.TestCase):
    
    def test_valid_schema(self):
        df = pd.DataFrame({
            'interaction_id': ['1'],
            'timestamp': [1.0],
            'facial_valence': [0.5],
            'vocal_energy': [0.5]
        })
        self.assertTrue(validate_feature_input(df))
    
    def test_missing_column(self):
        df = pd.DataFrame({
            'interaction_id': ['1'],
            'timestamp': [1.0],
            'facial_valence': [0.5]
            # missing vocal_energy
        })
        self.assertFalse(validate_feature_input(df))

if __name__ == '__main__':
    unittest.main()