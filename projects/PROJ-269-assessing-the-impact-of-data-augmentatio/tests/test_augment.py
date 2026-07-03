"""
Unit tests for data augmentation functions in code/augment.py.

Tests cover:
- Gaussian noise injection
- SMOTE edge cases (zero variance, small samples)
- Random oversampling
- Zero-variance sample handling
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from augment import (
    inject_gaussian_noise,
    apply_smote,
    apply_random_oversampling,
    augment_dataset,
    _check_zero_variance,
    _detect_target_column
)


class TestGaussianNoiseInjection:
    """Tests for Gaussian noise injection functionality."""

    def test_noise_increases_variance(self):
        """Verify that adding noise increases feature variance."""
        np.random.seed(42)
        X = np.random.rand(100, 5)
        y = np.random.randint(0, 2, 100)
        
        X_noisy, y_out = inject_gaussian_noise(X, y, noise_std=0.5, random_state=42)
        
        # Variance should increase with noise
        orig_var = np.var(X)
        noisy_var = np.var(X_noisy)
        assert noisy_var > orig_var, "Noise should increase variance"
        
        # Shape should be preserved
        assert X_noisy.shape == X.shape
        assert y_out.shape == y.shape

    def test_noise_std_parameter(self):
        """Test that different noise std values produce different results."""
        X = np.ones((50, 3)) * 5.0  # Constant feature
        y = np.array([0] * 25 + [1] * 25)
        
        X1, _ = inject_gaussian_noise(X, y, noise_std=0.1, random_state=42)
        X2, _ = inject_gaussian_noise(X, y, noise_std=0.5, random_state=42)
        
        # Different noise levels should produce different outputs
        assert not np.allclose(X1, X2), "Different noise std should produce different results"

    def test_zero_noise_preserves_data(self):
        """Test that zero noise preserves original data."""
        X = np.random.rand(50, 3)
        y = np.random.randint(0, 2, 50)
        
        X_noisy, y_out = inject_gaussian_noise(X, y, noise_std=0.0, random_state=42)
        
        assert np.allclose(X_noisy, X), "Zero noise should preserve data"
        assert np.array_equal(y_out, y), "Target should be unchanged"


class TestSMOTE:
    """Tests for SMOTE functionality."""

    def test_smote_balances_classes(self):
        """Verify SMOTE balances imbalanced classes."""
        X = np.random.rand(100, 5)
        y = np.array([0] * 80 + [1] * 20)  # 80:20 imbalance
        
        X_res, y_res = apply_smote(X, y, random_state=42, k_neighbors=3)
        
        unique, counts = np.unique(y_res, return_counts=True)
        assert len(unique) == 2, "Should have 2 classes"
        assert counts[0] == counts[1], "SMOTE should balance classes"

    def test_smote_handles_zero_variance_features(self):
        """Test SMOTE with zero-variance features."""
        # Create data with one zero-variance column
        X = np.random.rand(50, 4)
        X[:, 2] = 5.0  # Zero variance
        y = np.array([0] * 30 + [1] * 20)
        
        # Should handle without crashing
        X_res, y_res = apply_smote(X, y, random_state=42, k_neighbors=3)
        
        assert X_res.shape[0] >= X.shape[0], "SMOTE should increase or maintain sample count"
        assert y_res.shape[0] == X_res.shape[0], "X and y shapes should match"

    def test_smote_fails_with_insufficient_samples(self):
        """Test SMOTE fails gracefully with too few samples."""
        X = np.random.rand(3, 5)
        y = np.array([0, 0, 1])  # Only 1 sample in minority class
        
        with pytest.raises(ValueError, match="at least 2 samples per class"):
            apply_smote(X, y, random_state=42)

    def test_smote_k_neighbors_adjustment(self):
        """Test that k_neighbors is adjusted when too large."""
        X = np.random.rand(20, 3)
        y = np.array([0] * 15 + [1] * 5)  # Minority class has 5 samples
        
        # k_neighbors=10 is too large for 5 samples, should adjust
        X_res, y_res = apply_smote(X, y, random_state=42, k_neighbors=10)
        
        assert X_res.shape[0] > X.shape[0], "SMOTE should have applied"


class TestRandomOversampling:
    """Tests for Random Oversampling functionality."""

    def test_random_oversampling_balances_classes(self):
        """Verify random oversampling balances classes."""
        X = np.random.rand(100, 5)
        y = np.array([0] * 80 + [1] * 20)
        
        X_res, y_res = apply_random_oversampling(X, y, random_state=42)
        
        unique, counts = np.unique(y_res, return_counts=True)
        assert counts[0] == counts[1], "Random oversampling should balance classes"

    def test_random_oversampling_preserves_original_samples(self):
        """Verify original samples are preserved in random oversampling."""
        X = np.random.rand(50, 3)
        y = np.array([0] * 40 + [1] * 10)
        
        X_res, y_res = apply_random_oversampling(X, y, random_state=42)
        
        # All original samples should be present
        for i in range(len(X)):
            assert np.any(np.all(X_res == X[i], axis=1)), "Original samples should be preserved"


class TestZeroVarianceHandling:
    """Tests for zero-variance feature handling."""

    def test_check_zero_variance_detection(self):
        """Test zero-variance column detection."""
        X = np.random.rand(100, 5)
        X[:, 2] = 5.0  # Zero variance
        X[:, 4] = 10.0  # Another zero variance
        
        zero_cols = _check_zero_variance(X)
        assert 2 in zero_cols, "Column 2 should be detected as zero variance"
        assert 4 in zero_cols, "Column 4 should be detected as zero variance"
        assert 0 not in zero_cols, "Column 0 should not be zero variance"

    def test_augment_dataset_removes_zero_variance(self):
        """Test that augment_dataset handles zero-variance features."""
        df = pd.DataFrame({
            'feature1': np.random.rand(50),
            'feature2': np.ones(50) * 5,  # Zero variance
            'feature3': np.random.rand(50),
            'target': np.array([0] * 30 + [1] * 20)
        })
        
        # Should not crash
        aug_df, method = augment_dataset(df, 'gaussian_noise', random_state=42)
        
        assert len(aug_df) == len(df), "Sample count should be preserved for noise"


class TestAugmentDataset:
    """Tests for the main augment_dataset function."""

    def test_detect_target_column_priority(self):
        """Test target column detection priority."""
        # Test 'target' priority
        df1 = pd.DataFrame({'target': [0, 1], 'class': [0, 1]})
        assert _detect_target_column(df1) == 'target'
        
        # Test 'class' priority when 'target' missing
        df2 = pd.DataFrame({'class': [0, 1], 'label': [0, 1]})
        assert _detect_target_column(df2) == 'class'
        
        # Test 'label' priority when 'target' and 'class' missing
        df3 = pd.DataFrame({'label': [0, 1], 'other': [1, 2]})
        assert _detect_target_column(df3) == 'label'
        
        # Test default to last column
        df4 = pd.DataFrame({'a': [1, 2], 'b': [3, 4], 'c': [5, 6]})
        assert _detect_target_column(df4) == 'c'

    def test_invalid_method_raises_error(self):
        """Test that invalid method raises ValueError."""
        df = pd.DataFrame({
            'feature1': np.random.rand(50),
            'target': np.array([0] * 30 + [1] * 20)
        })
        
        with pytest.raises(ValueError, match="Unknown augmentation method"):
            augment_dataset(df, method='invalid_method')

    def test_gaussian_noise_output_shape(self):
        """Test Gaussian noise preserves shape."""
        df = pd.DataFrame({
            'f1': np.random.rand(100),
            'f2': np.random.rand(100),
            'target': np.array([0] * 60 + [1] * 40)
        })
        
        aug_df, _ = augment_dataset(df, 'gaussian_noise', random_state=42)
        
        assert aug_df.shape == df.shape, "Shape should be preserved"

    def test_smote_increases_samples(self):
        """Test that SMOTE increases sample count."""
        df = pd.DataFrame({
            'f1': np.random.rand(100),
            'f2': np.random.rand(100),
            'target': np.array([0] * 80 + [1] * 20)
        })
        
        aug_df, _ = augment_dataset(df, 'smote', random_state=42)
        
        assert aug_df.shape[0] > df.shape[0], "SMOTE should increase sample count"

    def test_random_oversampling_increases_samples(self):
        """Test that random oversampling increases sample count."""
        df = pd.DataFrame({
            'f1': np.random.rand(100),
            'f2': np.random.rand(100),
            'target': np.array([0] * 80 + [1] * 20)
        })
        
        aug_df, _ = augment_dataset(df, 'random_oversampling', random_state=42)
        
        assert aug_df.shape[0] > df.shape[0], "Random oversampling should increase sample count"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])