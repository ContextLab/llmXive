import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.classification.models import ClassificationModels

class TestStabilitySelection:
    """Unit tests for Stability Selection implementation."""
    
    def test_stability_selection_initialization(self):
        """Test that Stability Selection initializes with correct parameters."""
        selector = ClassificationModels(
            n_subsamples=50,
            sample_fraction=0.7,
            penalty_threshold=0.65
        )
        assert selector.n_subsamples == 50
        assert selector.sample_fraction == 0.7
        assert selector.penalty_threshold == 0.65
        assert selector.random_state == 42
        
    def test_stability_selection_with_known_features(self):
        """
        Test that stability selection correctly identifies strong features.
        Create a dataset where only the first 3 features are predictive.
        """
        np.random.seed(42)
        n_samples = 100
        n_features = 10
        
        # Create features where first 3 are predictive
        X = np.random.randn(n_samples, n_features)
        # True signal in first 3 features
        true_signal = X[:, 0] * 2 + X[:, 1] * 1.5 + X[:, 2] * 1.0
        y = (true_signal + np.random.randn(n_samples) * 0.5 > 0).astype(int)
        
        # Run stability selection
        selector = ClassificationModels(
            n_subsamples=20,  # Fewer for faster test
            sample_fraction=0.5,
            penalty_threshold=0.4,
            random_state=42
        )
        
        selected_indices, freqs = selector.run_stability_selection(X, y)
        
        # Check that we selected at least some of the true features
        # (with high probability given the strong signal)
        true_features_selected = any(i in selected_indices for i in [0, 1, 2])
        assert true_features_selected, "Should select at least one true feature"
        
        # Check that noise features (indices 3-9) are less likely to be selected
        # than true features (this is probabilistic, so we check the trend)
        true_freqs = freqs[[0, 1, 2]]
        noise_freqs = freqs[3:]
        
        # True features should generally have higher frequencies
        assert np.mean(true_freqs) > np.mean(noise_freqs), \
            "True features should have higher selection frequency than noise"
            
    def test_selection_frequency_threshold(self):
        """Test that the penalty threshold correctly filters features."""
        np.random.seed(42)
        n_samples = 50
        n_features = 5
        
        # Create random data
        X = np.random.randn(n_samples, n_features)
        y = np.random.randint(0, 2, n_samples)
        
        # Very high threshold should select few/no features
        selector_high = ClassificationModels(
            n_subsamples=10,
            sample_fraction=0.5,
            penalty_threshold=0.9,
            random_state=42
        )
        selected_high, _ = selector_high.run_stability_selection(X, y)
        
        # Very low threshold should select more features
        selector_low = ClassificationModels(
            n_subsamples=10,
            sample_fraction=0.5,
            penalty_threshold=0.1,
            random_state=42
        )
        selected_low, _ = selector_low.run_stability_selection(X, y)
        
        # With random data, high threshold should select fewer (or equal) features
        assert len(selected_high) <= len(selected_low), \
            "Higher threshold should select fewer or equal features"
            
    def test_save_stable_features(self, tmp_path):
        """Test that stable features are saved correctly to CSV."""
        selector = ClassificationModels()
        selected_indices = np.array([0, 2, 5])
        
        output_path = tmp_path / "stable_features.csv"
        selector.save_stable_features(selected_indices, output_path)
        
        # Verify file exists
        assert output_path.exists(), "Output file should be created"
        
        # Verify content
        df = pd.read_csv(output_path)
        assert 'feature_index' in df.columns, "Should have 'feature_index' column"
        assert 'selected' in df.columns, "Should have 'selected' column"
        assert len(df) == 3, "Should have 3 rows"
        assert list(df['feature_index']) == [0, 2, 5], "Should contain correct indices"
            
    def test_empty_selection(self):
        """Test behavior when no features pass the threshold."""
        np.random.seed(42)
        n_samples = 30
        n_features = 5
        
        # Create completely random data (no signal)
        X = np.random.randn(n_samples, n_features)
        y = np.random.randint(0, 2, n_samples)
        
        # Very high threshold
        selector = ClassificationModels(
            n_subsamples=10,
            sample_fraction=0.5,
            penalty_threshold=0.95,
            random_state=42
        )
        
        selected_indices, freqs = selector.run_stability_selection(X, y)
        
        # May or may not select features with random data, but should not crash
        assert isinstance(selected_indices, np.ndarray), "Should return numpy array"
        assert len(selected_indices) >= 0, "Should have non-negative length"
        assert freqs.shape == (n_features,), "Should return frequencies for all features"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
