"""
tests/unit/test_compute_metrics.py

Unit tests for the intra-modal consistency metric calculation.
Uses a deterministic mock timeseries file to avoid external dependencies
while ensuring the logic runs against real numeric data.
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

# Ensure fixture directory exists and contains the mock data
FIXTURE_PATH = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'mock_timeseries.npy')
if not os.path.exists(FIXTURE_PATH):
    os.makedirs(os.path.dirname(FIXTURE_PATH), exist_ok=True)
    # Generate deterministic mock data if missing
    # Shape: (N_interactions, N_timepoints, 2_features)
    # Features: [facial_valence, vocal_energy]
    rng = np.random.default_rng(seed=42)
    N = 10
    T = 100
    mock_data = rng.standard_normal((N, T, 2))
    # Inject a known correlation in the first interaction
    mock_data[0, :, 1] = mock_data[0, :, 0] * 0.8 + rng.standard_normal(T) * 0.1
    np.save(FIXTURE_PATH, mock_data)

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

    def test_mock_timeseries_loading(self):
        """Test processing against the actual mock timeseries fixture."""
        # Load the deterministic mock data
        data = np.load(FIXTURE_PATH)
        # Create a DataFrame from the first interaction (known correlation)
        # data shape: (N, T, 2) -> (T, 2) for one interaction
        ts = data[0] 
        df = pd.DataFrame({
            'interaction_id': ['int-mock'] * len(ts),
            'timestamp': np.arange(len(ts)),
            'facial_valence': ts[:, 0],
            'vocal_energy': ts[:, 1]
        })
        
        result = process_interaction_features(df, 'int-mock')
        self.assertIsNotNone(result)
        self.assertEqual(result['interaction_id'], 'int-mock')
        # We injected a strong correlation, so score should be > 0.5
        self.assertGreater(result['consistency_score'], 0.5)

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