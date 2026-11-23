"""
Unit tests for data augmentation utilities.

Tests for masking logic, DAE batch creation, and mask statistics.
"""
import pytest
import random
from typing import List
import numpy as np

# Import the functions to test
from data.augment import (
    apply_dae_mask,
    create_dae_batch,
    calculate_mask_statistics,
    MASK_RATE
)
from config import Config


class TestMaskRateConstant:
    """Test that MASK_RATE constant is correctly defined."""
    
    def test_mask_rate_value(self):
        """Verify MASK_RATE is set to 0.15 as per T013a."""
        assert MASK_RATE == 0.15, f"Expected MASK_RATE to be 0.15, got {MASK_RATE}"
    
    def test_mask_rate_in_config(self):
        """Verify MASK_RATE is also defined in Config."""
        config = Config()
        assert config.MASK_RATE == 0.15, "Config.MASK_RATE should match augment.MASK_RATE"


class TestApplyDAEMask:
    """Tests for the apply_dae_mask function."""
    
    def test_empty_input(self):
        """Test masking with empty input."""
        masked_ids, mask_positions = apply_dae_mask([])
        assert masked_ids == []
        assert mask_positions == []
    
    def test_single_token(self):
        """Test masking with a single token."""
        input_ids = [101]
        masked_ids, mask_positions = apply_dae_mask(input_ids, mask_rate=1.0, seed=42)
        assert len(masked_ids) == 1
        assert len(mask_positions) == 1
        assert mask_positions[0] == True  # Should be masked with 100% rate
    
    def test_mask_rate_consistency(self):
        """Test that mask rate is approximately maintained over many trials."""
        input_ids = list(range(1000))
        total_masks = 0
        trials = 100
        
        for i in range(trials):
            _, mask_positions = apply_dae_mask(
                input_ids, 
                mask_rate=0.15, 
                seed=i
            )
            total_masks += sum(mask_positions)
        
        avg_masks = total_masks / trials
        expected_masks = len(input_ids) * 0.15
        
        # Allow 10% tolerance for randomness
        assert abs(avg_masks - expected_masks) / expected_masks < 0.1, \
            f"Average masks {avg_masks} differs significantly from expected {expected_masks}"
    
    def test_mask_positions_are_boolean(self):
        """Test that mask_positions contains boolean values."""
        input_ids = [101, 102, 103, 104, 105]
        _, mask_positions = apply_dae_mask(input_ids, seed=42)
        
        for pos in mask_positions:
            assert isinstance(pos, bool), f"Mask position {pos} is not boolean"
    
    def test_reproducibility_with_seed(self):
        """Test that same seed produces same results."""
        input_ids = [101, 102, 103, 104, 105, 106, 107, 108, 109, 110]
        
        masked1, mask1 = apply_dae_mask(input_ids, seed=123)
        masked2, mask2 = apply_dae_mask(input_ids, seed=123)
        
        assert masked1 == masked2, "Same seed should produce same masked IDs"
        assert mask1 == mask2, "Same seed should produce same mask positions"
    
    def test_mask_token_replacement(self):
        """Test that masked tokens are replaced with MASK token."""
        input_ids = [101, 102, 103, 104, 105]
        # Force 100% masking to ensure all tokens are masked
        masked_ids, mask_positions = apply_dae_mask(
            input_ids, 
            mask_rate=1.0, 
            random_replace_rate=0.0,  # No random replacement
            keep_original_rate=0.0,   # No keep original
            seed=42
        )
        
        # All positions should be masked
        assert all(mask_positions)
        
        # Masked tokens should be MASK_TOKEN_ID (103)
        # Note: Some might be kept original due to the 10% rule, but with 0.0 rates,
        # they should all be masked
        mask_token_id = 103
        masked_count = sum(1 for id in masked_ids if id == mask_token_id)
        # At least 80% should be mask tokens (80% of masked tokens)
        assert masked_count >= len(input_ids) * 0.8


class TestCreateDAEBatch:
    """Tests for the create_dae_batch function."""
    
    def test_batch_creation(self):
        """Test creating a batch of masked sequences."""
        batch = [
            [101, 102, 103, 104, 105],
            [101, 202, 203, 204, 205],
            [101, 302, 303, 304, 305]
        ]
        
        masked_batch, mask_positions_batch, original_batch = create_dae_batch(
            batch, 
            seed=42
        )
        
        assert len(masked_batch) == len(batch)
        assert len(mask_positions_batch) == len(batch)
        assert len(original_batch) == len(batch)
        
        # Original batch should be unchanged
        assert original_batch == batch
        
        # All sequences should have same length as input
        for i, orig in enumerate(original_batch):
            assert len(masked_batch[i]) == len(orig)
            assert len(mask_positions_batch[i]) == len(orig)
    
    def test_batch_reproducibility(self):
        """Test that same seed produces same batch results."""
        batch = [
            [101, 102, 103, 104, 105],
            [101, 202, 203, 204, 205]
        ]
        
        masked1, mask1, orig1 = create_dae_batch(batch, seed=999)
        masked2, mask2, orig2 = create_dae_batch(batch, seed=999)
        
        assert masked1 == masked2
        assert mask1 == mask2
        assert orig1 == orig2


class TestCalculateMaskStatistics:
    """Tests for the calculate_mask_statistics function."""
    
    def test_statistics_calculation(self):
        """Test that statistics are calculated correctly."""
        input_ids = list(range(100))
        stats = calculate_mask_statistics(input_ids, mask_rate=0.15)
        
        assert stats["total_tokens"] == 100
        assert stats["expected_masks"] == 15
        assert stats["mask_rate"] == 0.15
        assert stats["min_masks"] == 14
        assert stats["max_masks"] == 16
    
    def test_empty_input_statistics(self):
        """Test statistics with empty input."""
        stats = calculate_mask_statistics([])
        
        assert stats["total_tokens"] == 0
        assert stats["expected_masks"] == 0
        assert stats["min_masks"] == 1  # max(1, -1) = 1
        assert stats["max_masks"] == 1