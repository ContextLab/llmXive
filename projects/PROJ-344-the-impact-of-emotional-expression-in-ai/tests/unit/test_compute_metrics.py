import pytest
import numpy as np
import pandas as pd
import os
import sys
from pathlib import Path

# Add code directory to path for imports
code_path = Path(__file__).parent.parent / 'code'
sys.path.insert(0, str(code_path))

from compute_metrics import (
    validate_feature_input,
    compute_max_abs_cross_correlation,
    compute_consistency_score,
    process_interaction_features
)

class TestValidateFeatureInput:
    def test_valid_input(self):
        df = pd.DataFrame({
            'interaction_id': ['1', '2'],
            'timestamp': [0.0, 1.0],
            'facial_valence': [0.5, 0.6],
            'facial_energy': [0.1, 0.2],
            'vocal_pitch': [100.0, 101.0],
            'vocal_energy': [0.5, 0.6]
        })
        assert validate_feature_input(df) is True

    def test_missing_column(self):
        df = pd.DataFrame({
            'interaction_id': ['1'],
            'timestamp': [0.0],
            'facial_valence': [0.5]
        })
        assert validate_feature_input(df) is False

    def test_empty_dataframe(self):
        df = pd.DataFrame()
        assert validate_feature_input(df) is False

class TestComputeMaxAbsCrossCorrelation:
    def test_perfect_correlation_zero_lag(self):
        # Two identical signals should have correlation 1.0 at lag 0
        signal = np.random.randn(100)
        fs = 10.0
        corr, lag = compute_max_abs_cross_correlation(signal, signal, fs)
        assert np.isclose(corr, 1.0, atol=0.01)
        assert np.isclose(lag, 0.0, atol=0.1)

    def test_shifted_signal(self):
        # Shift signal by 1 second (10 samples at 10Hz)
        signal = np.random.randn(200)
        shifted = np.roll(signal, 10)
        fs = 10.0
        corr, lag = compute_max_abs_cross_correlation(signal, shifted, fs)
        # Should find high correlation at lag ~1.0s
        assert corr > 0.8
        assert 0.8 < lag < 1.2

    def test_different_lengths(self):
        with pytest.raises(ValueError):
            compute_max_abs_cross_correlation(np.array([1, 2]), np.array([1, 2, 3]), 1.0)

class TestComputeConsistencyScore:
    def test_basic_computation(self):
        facial = np.random.randn(100)
        vocal = np.random.randn(100)
        scores = compute_consistency_score(facial, vocal, 10.0)
        assert 'consistency_score' in scores
        assert 'facial_valence_vocal_energy_corr' in scores
        assert 0 <= scores['consistency_score'] <= 1.0

class TestProcessInteractionFeatures:
    def test_single_interaction(self):
        df = pd.DataFrame({
            'interaction_id': ['A'] * 100,
            'timestamp': np.linspace(0, 10, 100),
            'facial_valence': np.random.randn(100),
            'facial_energy': np.random.randn(100),
            'vocal_pitch': np.random.randn(100),
            'vocal_energy': np.random.randn(100)
        })
        result = process_interaction_features(df)
        assert len(result) == 1
        assert result.iloc[0]['interaction_id'] == 'A'
        assert 'consistency_score' in result.columns

    def test_multiple_interactions(self):
        df = pd.DataFrame({
            'interaction_id': ['A'] * 50 + ['B'] * 50,
            'timestamp': list(np.linspace(0, 5, 50)) + list(np.linspace(0, 5, 50)),
            'facial_valence': np.random.randn(100),
            'facial_energy': np.random.randn(100),
            'vocal_pitch': np.random.randn(100),
            'vocal_energy': np.random.randn(100)
        })
        result = process_interaction_features(df)
        assert len(result) == 2
        assert set(result['interaction_id']) == {'A', 'B'}

    def test_invalid_input(self):
        df = pd.DataFrame({
            'interaction_id': ['A'],
            'timestamp': [0.0],
            'facial_valence': [0.5]
            # Missing required columns
        })
        with pytest.raises(ValueError):
            process_interaction_features(df)

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
