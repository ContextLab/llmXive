import pytest
import numpy as np
import pandas as pd
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from classification.models import StabilitySelection

class TestStabilitySelection:
    """Unit tests for the StabilitySelection class."""

    def test_fit_basic(self):
        """Test basic fitting of StabilitySelection."""
        # Create synthetic data
        np.random.seed(42)
        n_samples, n_features = 60, 10
        X = np.random.randn(n_samples, n_features)
        y = np.random.randint(0, 2, n_samples)
        
        # Initialize and fit
        ss = StabilitySelection(n_subsamples=10, sample_size=30, random_state=42)
        ss.fit(X, y)
        
        # Verify attributes exist
        assert ss.selection_frequencies_ is not None
        assert ss.selected_features_mask_ is not None
        assert ss.selected_indices_ is not None
        assert len(ss.selection_frequencies_) == n_features
        assert len(ss.selected_indices_) >= 0

    def test_sample_size_validation(self):
        """Test that sample_size > n_samples raises an error."""
        X = np.random.randn(10, 5)
        y = np.random.randint(0, 2, 10)
        
        ss = StabilitySelection(sample_size=20)  # > 10 samples
        
        with pytest.raises(ValueError, match="Sample size"):
            ss.fit(X, y)

    def test_selection_threshold_logic(self):
        """Test that features are selected based on threshold."""
        # Create data where one feature is highly predictive
        np.random.seed(42)
        n_samples, n_features = 60, 5
        X = np.random.randn(n_samples, n_features)
        # Make first feature strongly correlated with label
        y = (X[:, 0] > 0).astype(int)
        
        ss = StabilitySelection(
            n_subsamples=50, 
            sample_size=30, 
            selection_threshold=0.60,
            random_state=42
        )
        ss.fit(X, y)
        
        # The first feature should have a higher frequency
        assert ss.selection_frequencies_[0] >= ss.selection_frequencies_[1:].mean()

    def test_get_selected_features(self):
        """Test retrieval of selected feature indices."""
        np.random.seed(42)
        X = np.random.randn(60, 10)
        y = np.random.randint(0, 2, 60)
        
        ss = StabilitySelection(n_subsamples=20, sample_size=30, random_state=42)
        ss.fit(X, y)
        
        indices = ss.get_selected_features()
        assert isinstance(indices, np.ndarray)
        assert all(0 <= idx < 10 for idx in indices)

    def test_empty_selection(self):
        """Test behavior when no features pass threshold."""
        # Use a very high threshold
        np.random.seed(42)
        X = np.random.randn(60, 10)
        y = np.random.randint(0, 2, 60)
        
        ss = StabilitySelection(
            n_subsamples=20, 
            sample_size=30, 
            selection_threshold=0.99,  # Very high
            random_state=42
        )
        ss.fit(X, y)
        
        # May select 0 features
        assert len(ss.get_selected_features()) >= 0

    def test_frequencies_sum(self):
        """Test that frequencies are between 0 and 1."""
        np.random.seed(42)
        X = np.random.randn(60, 10)
        y = np.random.randint(0, 2, 60)
        
        ss = StabilitySelection(n_subsamples=50, sample_size=30, random_state=42)
        ss.fit(X, y)
        
        freqs = ss.get_frequencies()
        assert np.all(freqs >= 0.0)
        assert np.all(freqs <= 1.0)
        assert len(freqs) == X.shape[1]

    def test_deterministic_with_seed(self):
        """Test that results are deterministic with fixed random_state."""
        np.random.seed(42)
        X = np.random.randn(60, 10)
        y = np.random.randint(0, 2, 60)
        
        ss1 = StabilitySelection(n_subsamples=20, sample_size=30, random_state=42)
        ss1.fit(X, y)
        
        ss2 = StabilitySelection(n_subsamples=20, sample_size=30, random_state=42)
        ss2.fit(X, y)
        
        # Results should be identical
        np.testing.assert_array_equal(ss1.selection_frequencies_, ss2.selection_frequencies_)
        np.testing.assert_array_equal(ss1.selected_indices_, ss2.selected_indices_)