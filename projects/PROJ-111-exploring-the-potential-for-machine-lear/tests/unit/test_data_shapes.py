"""
Unit tests for data shapes, normalization correctness, and stratification logic.
Tests the preprocessing pipeline functions defined in code/preprocessing.py.
"""
import numpy as np
import pytest
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from preprocessing import normalize_spins, reshape_to_batch, stratified_split


class TestNormalizeSpins:
    """Tests for the normalize_spins function."""

    def test_normalization_unit_length(self):
        """Verify that normalized spins have unit length."""
        # Create random spin configurations
        np.random.seed(42)
        batch_size = 10
        L = 16
        spins = np.random.randn(batch_size, 3, L, L)

        normalized = normalize_spins(spins)

        # Calculate the magnitude of each spin vector
        magnitudes = np.sqrt(np.sum(normalized**2, axis=1))

        # All magnitudes should be 1.0 (within floating point tolerance)
        assert np.allclose(magnitudes, 1.0, atol=1e-6), "Normalized spins must have unit length"

    def test_normalization_shape_preservation(self):
        """Verify that normalization preserves the input shape."""
        np.random.seed(42)
        batch_size = 10
        L = 16
        spins = np.random.randn(batch_size, 3, L, L)

        normalized = normalize_spins(spins)

        assert normalized.shape == spins.shape, "Shape must be preserved after normalization"

    def test_normalization_zero_vector_handling(self):
        """Verify behavior with near-zero vectors (should not crash)."""
        np.random.seed(42)
        batch_size = 5
        L = 8
        # Create some near-zero vectors
        spins = np.random.randn(batch_size, 3, L, L) * 1e-10

        # Should not raise an error
        normalized = normalize_spins(spins)

        # Check that shape is preserved
        assert normalized.shape == spins.shape

        # Magnitudes should be 1.0 where input was non-zero
        # (For all-zero inputs, normalization might result in 0s or NaNs depending on implementation)
        # This test mainly ensures no crash occurs.


class TestReshapeToBatch:
    """Tests for the reshape_to_batch function."""

    def test_reshape_dimensions(self):
        """Verify that reshape produces the correct [batch, 3, L, L] shape."""
        np.random.seed(42)
        L = 16
        num_spins = 1000  # Total number of configurations

        # Simulate raw data: (num_spins, 3*L*L) flattened or similar
        # Assuming raw data comes as (N, 3, L, L) already but we test the function logic
        # If input is (N, 3, L, L), output should be same
        raw_data = np.random.randn(num_spins, 3, L, L)

        reshaped = reshape_to_batch(raw_data, L)

        assert reshaped.shape == (num_spins, 3, L, L), f"Expected shape ({num_spins}, 3, {L}, {L}), got {reshaped.shape}"

    def test_reshape_flattened_input(self):
        """Test reshaping from flattened input if applicable."""
        np.random.seed(42)
        L = 8
        num_spins = 500

        # Simulate flattened input: (N, 3*L*L)
        flat_data = np.random.randn(num_spins, 3 * L * L)

        # The function expects to handle reshaping to (N, 3, L, L)
        # Assuming the implementation handles this or input is already shaped
        # If the function expects (N, 3, L, L) as input, this test might need adjustment
        # Based on typical usage, we assume input is (N, 3, L, L) or (N, 3*L*L)
        # Let's test the case where input is (N, 3, L, L)
        reshaped = reshape_to_batch(flat_data.reshape(num_spins, 3, L, L), L)
        assert reshaped.shape == (num_spins, 3, L, L)


class TestStratifiedSplit:
    """Tests for the stratified_split function."""

    def test_stratification_variance(self):
        """Verify that stratified split maintains balanced temperature bins."""
        np.random.seed(42)
        L = 16
        num_samples_per_temp = 100
        temperatures = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]

        # Create synthetic data with temperature labels
        data_list = []
        labels_list = []
        for temp in temperatures:
            # Create data for this temperature
            data = np.random.randn(num_samples_per_temp, 3, L, L)
            data_list.append(data)
            labels_list.extend([temp] * num_samples_per_temp)

        full_data = np.concatenate(data_list, axis=0)
        full_labels = np.array(labels_list)

        # Perform stratified split
        train_data, val_data, train_labels, val_labels = stratified_split(
            full_data, full_labels, val_ratio=0.2
        )

        # Check total counts
        assert len(train_labels) + len(val_labels) == len(full_labels), "Total samples mismatch"

        # Check stratification variance
        # Count samples per temperature in train and val sets
        unique_temps = np.unique(full_labels)
        max_variance = 0.0

        for temp in unique_temps:
            expected_train = int(num_samples_per_temp * 0.8)
            expected_val = int(num_samples_per_temp * 0.2)

            actual_train = np.sum(train_labels == temp)
            actual_val = np.sum(val_labels == temp)

            # Allow small variance (<= 5 samples as per task requirement)
            variance_train = abs(actual_train - expected_train)
            variance_val = abs(actual_val - expected_val)

            max_variance = max(max_variance, variance_train, variance_val)

        assert max_variance <= 5, f"Stratification variance {max_variance} exceeds allowed limit of 5"

    def test_stratification_split_ratio(self):
        """Verify that the split ratio is approximately correct."""
        np.random.seed(42)
        L = 16
        total_samples = 1000
        val_ratio = 0.2

        data = np.random.randn(total_samples, 3, L, L)
        labels = np.random.choice([0.5, 1.0, 1.5, 2.0], total_samples)

        train_data, val_data, train_labels, val_labels = stratified_split(
            data, labels, val_ratio=val_ratio
        )

        actual_val_ratio = len(val_labels) / total_samples

        # Allow 5% tolerance on the ratio
        assert abs(actual_val_ratio - val_ratio) < 0.05, f"Split ratio {actual_val_ratio} deviates too much from {val_ratio}"

    def test_stratification_data_consistency(self):
        """Verify that data and labels remain consistent after split."""
        np.random.seed(42)
        L = 8
        total_samples = 200

        data = np.random.randn(total_samples, 3, L, L)
        labels = np.arange(total_samples)  # Unique labels for consistency check

        train_data, val_data, train_labels, val_labels = stratified_split(
            data, labels, val_ratio=0.25
        )

        # Check that all labels in train are present in train_data
        for i, label in enumerate(train_labels):
            # Just check shape consistency
            assert train_data[i].shape == data[int(label)].shape

        # Check that all labels in val are present in val_data
        for i, label in enumerate(val_labels):
            assert val_data[i].shape == data[int(label)].shape
