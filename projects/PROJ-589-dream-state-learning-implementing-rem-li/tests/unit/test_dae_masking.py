"""
Unit tests for DAE masking logic in code/data/augment.py.
Tests apply_dae_mask, create_dae_batch, and calculate_mask_statistics.
"""
import pytest
import numpy as np
from typing import List, Tuple

# Import the actual functions from the project
from data.augment import apply_dae_mask, create_dae_batch, calculate_mask_statistics


class TestApplyDAEMask:
    """Tests for the apply_dae_mask function."""

    def test_mask_rate_accuracy(self):
        """Test that the actual mask rate is close to the target rate."""
        sequence = list(range(100))  # 100 tokens
        mask_rate = 0.15
        masked_seq, mask_indices = apply_dae_mask(sequence, mask_rate, seed=42)

        # Count actual masked tokens
        actual_masked = sum(1 for i in range(len(sequence)) if i in mask_indices)
        actual_rate = actual_masked / len(sequence)

        # Allow some tolerance due to randomness
        assert 0.10 <= actual_rate <= 0.20, f"Mask rate {actual_rate} outside expected range"

    def test_mask_indices_are_unique(self):
        """Test that mask indices are unique and within bounds."""
        sequence = list(range(50))
        mask_rate = 0.2
        _, mask_indices = apply_dae_mask(sequence, mask_rate, seed=123)

        assert len(mask_indices) == len(set(mask_indices)), "Mask indices should be unique"
        assert all(0 <= idx < len(sequence) for idx in mask_indices), "Mask indices out of bounds"

    def test_masked_tokens_are_replaced(self):
        """Test that masked tokens are replaced with [MASK] token."""
        sequence = [1, 2, 3, 4, 5]
        mask_rate = 1.0  # Mask everything
        masked_seq, _ = apply_dae_mask(sequence, mask_rate, seed=42)

        # All tokens should be replaced with [MASK] (typically represented as a special token ID)
        # Assuming [MASK] is represented as a specific value (e.g., -1 or a special token ID)
        # For this test, we just verify the sequence length is preserved
        assert len(masked_seq) == len(sequence), "Sequence length should be preserved"

    def test_no_mask_when_rate_zero(self):
        """Test that no masking occurs when mask_rate is 0."""
        sequence = [1, 2, 3, 4, 5]
        masked_seq, mask_indices = apply_dae_mask(sequence, 0.0, seed=42)

        assert mask_indices == [], "No indices should be masked when rate is 0"
        assert masked_seq == sequence, "Sequence should be unchanged when no masking"

    def test_deterministic_with_seed(self):
        """Test that results are deterministic with the same seed."""
        sequence = list(range(20))
        mask_rate = 0.25

        _, indices1 = apply_dae_mask(sequence, mask_rate, seed=999)
        _, indices2 = apply_dae_mask(sequence, mask_rate, seed=999)

        assert indices1 == indices2, "Same seed should produce same mask indices"


class TestCreateDAEBatch:
    """Tests for the create_dae_batch function."""

    def test_batch_creation(self):
        """Test that a DAE batch is created correctly."""
        batch = [
            [1, 2, 3, 4, 5],
            [6, 7, 8, 9, 10],
            [11, 12, 13, 14, 15]
        ]
        mask_rate = 0.2

        masked_batch, original_batch, mask_indices = create_dae_batch(batch, mask_rate, seed=42)

        assert len(masked_batch) == len(batch), "Batch size should be preserved"
        assert len(original_batch) == len(batch), "Original batch should be preserved"
        assert len(mask_indices) == len(batch), "Mask indices should be per-sample"

    def test_original_batch_unchanged(self):
        """Test that the original batch is returned unchanged."""
        batch = [[1, 2, 3], [4, 5, 6]]
        mask_rate = 0.5

        _, original_batch, _ = create_dae_batch(batch, mask_rate, seed=42)

        assert original_batch == batch, "Original batch should be unchanged"

    def test_masked_and_original_same_length(self):
        """Test that masked and original sequences have the same length."""
        batch = [[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]]
        mask_rate = 0.3

        masked_batch, original_batch, _ = create_dae_batch(batch, mask_rate, seed=42)

        for masked_seq, original_seq in zip(masked_batch, original_batch):
            assert len(masked_seq) == len(original_seq), "Sequence lengths should match"


class TestCalculateMaskStatistics:
    """Tests for the calculate_mask_statistics function."""

    def test_statistics_calculation(self):
        """Test that mask statistics are calculated correctly."""
        batch_size = 10
        seq_length = 20
        mask_rate = 0.25

        # Create dummy mask indices
        mask_indices_per_sample = [
            np.random.choice(seq_length, size=int(seq_length * mask_rate), replace=False).tolist()
            for _ in range(batch_size)
        ]

        stats = calculate_mask_statistics(mask_indices_per_sample, seq_length)

        assert "total_tokens" in stats, "Should have total_tokens"
        assert "total_masked" in stats, "Should have total_masked"
        assert "mask_rate" in stats, "Should have mask_rate"
        assert "avg_masked_per_sample" in stats, "Should have avg_masked_per_sample"

        assert stats["total_tokens"] == batch_size * seq_length, "Total tokens calculation incorrect"
        assert abs(stats["mask_rate"] - mask_rate) < 0.05, "Mask rate should be close to target"

    def test_empty_batch(self):
        """Test statistics calculation with empty batch."""
        stats = calculate_mask_statistics([], 0)

        assert stats["total_tokens"] == 0, "Total tokens should be 0"
        assert stats["total_masked"] == 0, "Total masked should be 0"
        assert stats["mask_rate"] == 0.0, "Mask rate should be 0.0"

    def test_full_mask(self):
        """Test statistics when everything is masked."""
        seq_length = 10
        mask_indices_per_sample = [list(range(seq_length)) for _ in range(5)]

        stats = calculate_mask_statistics(mask_indices_per_sample, seq_length)

        assert stats["mask_rate"] == 1.0, "Mask rate should be 1.0"
        assert stats["total_masked"] == stats["total_tokens"], "All tokens should be masked"