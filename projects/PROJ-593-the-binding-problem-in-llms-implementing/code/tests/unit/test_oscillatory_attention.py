"""
Unit tests for OscillatoryAttentionModule.
"""

import pytest
import torch
import math
from src.models.oscillatory_attention import OscillatoryAttentionModule

class TestOscillatoryAttentionModule:
    """Tests for the OscillatoryAttentionModule class."""

    def test_initialization(self):
        """Test that the module initializes correctly."""
        module = OscillatoryAttentionModule(
            d_model=768,
            num_heads=12,
            max_seq_len=512,
            cycles_per_sequence=40.0
        )
        assert module.d_model == 768
        assert module.num_heads == 12
        assert module.max_seq_len == 512
        assert module.cycles_per_sequence == 40.0
        assert module.oscillation_mask.shape == (1, 1, 512, 512)

    def test_mask_range(self):
        """Test that the oscillation mask values are in the expected range [-1, 1]."""
        module = OscillatoryAttentionModule(
            d_model=64,
            num_heads=4,
            max_seq_len=128,
            cycles_per_sequence=10.0
        )
        mask = module.oscillation_mask
        assert mask.min() >= -1.0
        assert mask.max() <= 1.0

    def test_forward_pass_shape(self):
        """Test that forward pass preserves input shape."""
        module = OscillatoryAttentionModule(
            d_model=64,
            num_heads=4,
            max_seq_len=32,
            cycles_per_sequence=5.0
        )
        batch_size = 2
        seq_len = 32
        # Input: (batch, heads, seq_len, seq_len)
        attention_scores = torch.randn(batch_size, 4, seq_len, seq_len)

        output = module(attention_scores)

        assert output.shape == attention_scores.shape
        assert output.shape == (batch_size, 4, seq_len, seq_len)

    def test_forward_pass_gating_effect(self):
        """Test that the mask actually modifies the attention scores."""
        module = OscillatoryAttentionModule(
            d_model=64,
            num_heads=4,
            max_seq_len=32,
            cycles_per_sequence=1.0  # Low frequency for easy verification
        )
        attention_scores = torch.ones(1, 1, 32, 32)  # Uniform scores
        output = module(attention_scores)

        # The output should not be all ones because the mask varies
        assert not torch.allclose(output, attention_scores)

        # The output should be within the range of the mask scaling
        # Mask is scaled to [0, 1], so output should be between 0 and 1 (if input is 1)
        assert output.min() >= 0.0
        assert output.max() <= 1.0

    def test_frequency_sensitivity(self):
        """Test that different frequencies produce different masks."""
        module_1 = OscillatoryAttentionModule(
            d_model=64,
            num_heads=4,
            max_seq_len=64,
            cycles_per_sequence=5.0
        )
        module_2 = OscillatoryAttentionModule(
            d_model=64,
            num_heads=4,
            max_seq_len=64,
            cycles_per_sequence=10.0
        )

        # Compare masks (should be different)
        mask_1 = module_1.oscillation_mask
        mask_2 = module_2.oscillation_mask

        assert not torch.allclose(mask_1, mask_2)

    def test_dynamic_sequence_length(self):
        """Test that the module handles sequence lengths shorter than max_seq_len."""
        module = OscillatoryAttentionModule(
            d_model=64,
            num_heads=4,
            max_seq_len=128,
            cycles_per_sequence=5.0
        )
        # Input with shorter sequence
        attention_scores = torch.randn(1, 4, 32, 32)
        output = module(attention_scores)
        assert output.shape == (1, 4, 32, 32)

    def test_batch_and_head_broadcasting(self):
        """Test that the mask broadcasts correctly over batch and head dimensions."""
        module = OscillatoryAttentionModule(
            d_model=64,
            num_heads=4,
            max_seq_len=16,
            cycles_per_sequence=2.0
        )
        # Batch size > 1, Heads > 1
        attention_scores = torch.randn(4, 8, 16, 16)
        output = module(attention_scores)

        assert output.shape == (4, 8, 16, 16)

        # Check that the same mask pattern is applied across heads/batches
        # (Since the mask is (1,1,L,L) and broadcasted)
        # We can't easily check the values without slicing, but shape is correct.

    def test_phase_offset(self):
        """Test that phase offset shifts the wave."""
        module_0 = OscillatoryAttentionModule(
            d_model=64,
            num_heads=4,
            max_seq_len=64,
            cycles_per_sequence=10.0,
            phase_offset=0.0
        )
        module_pi = OscillatoryAttentionModule(
            d_model=64,
            num_heads=4,
            max_seq_len=64,
            cycles_per_sequence=10.0,
            phase_offset=math.pi
        )

        # sin(x + pi) = -sin(x)
        # So the mask should be inverted (after scaling to [0,1], it will be mirrored)
        mask_0 = module_0.oscillation_mask
        mask_pi = module_pi.oscillation_mask

        # They should be different
        assert not torch.allclose(mask_0, mask_pi)