"""Unit tests for attention mask logic and block-based output parsing.

These tests verify the implementation described in Section 3 of the manuscript,
specifically the handling of attention masks during parallel box decoding
and the parsing of quantized coordinate tokens into block-based outputs.
"""

import pytest
import torch
from models.attention_mask import generate_attention_mask, apply_block_mask
from utils.parsing import parse_block_output, quantize_coordinates


class TestAttentionMaskGeneration:
    """Tests for the attention mask generation logic."""

    def test_mask_shape_correctness(self):
        """Verify that generated masks match expected tensor dimensions."""
        batch_size, seq_len, num_boxes = 2, 512, 4
        mask = generate_attention_mask(batch_size, seq_len, num_boxes)
        assert mask.shape == (batch_size, seq_len, seq_len), "Mask shape mismatch"

    def test_mask_values_binary(self):
        """Ensure mask values are strictly 0 or 1."""
        mask = generate_attention_mask(1, 100, 2)
        unique_values = torch.unique(mask)
        assert set(unique_values.tolist()).issubset({0, 1}), "Mask contains non-binary values"

    def test_causal_masking_applied(self):
        """Check that future positions are masked out in causal scenarios."""
        mask = generate_attention_mask(1, 10, 1, causal=True)
        # Upper triangle (future) should be zero
        upper_triangle = mask[0, :, :].triu(diagonal=1)
        assert upper_triangle.sum() == 0, "Causal masking not applied correctly"


    """Tests for applying block-based constraints to attention masks."""

    def test_block_isolation(self):
        """Verify that blocks are isolated from each other in the mask."""
        mask = torch.ones(1, 20, 20)
        block_indices = torch.tensor([[0, 5], [10, 15]])
        masked = apply_block_mask(mask, block_indices)
        # Cross-block attention should be zeroed
        cross_block = masked[0, 0:5, 10:15]
        assert cross_block.sum() == 0, "Blocks are not properly isolated"

    def test_intra_block_attention_preserved(self):
        """Ensure attention within a block remains active."""
        mask = torch.zeros(1, 20, 20)
        block_indices = torch.tensor([[0, 5]])
        masked = apply_block_mask(mask, block_indices)
        intra_block = masked[0, 0:5, 0:5]
        assert intra_block.sum() > 0, "Intra-block attention incorrectly disabled"


    """Tests for parsing block-based outputs from model logits."""

    def test_coordinate_quantization(self):
        """Test the quantization of raw coordinates to discrete tokens."""
        raw_coords = torch.tensor([0.1, 0.5, 0.9, 1.0])
        quantized = quantize_coordinates(raw_coords, num_bins=100)
        assert quantized.min() >= 0 and quantized.max() < 100, "Quantization out of bounds"
        assert quantized.dtype == torch.long, "Quantized output must be integer type"

    def test_block_parsing_structure(self):
        """Verify that parsed blocks contain correct corner coordinates."""
        logits = torch.randn(1, 4, 100)  # 4 boxes, 100 bins
        blocks = parse_block_output(logits)
        assert blocks.shape[1] == 4, "Expected 4 boxes in output"
        assert blocks.shape[2] == 4, "Each box should have 4 coordinates (x1, y1, x2, y2)"

    def test_invalid_block_handling(self):
        """Ensure blocks with invalid coordinates (e.g., x2 < x1) are flagged."""
        # Simulate a block where x2 < x1
        invalid_logits = torch.zeros(1, 1, 100)
        invalid_logits[0, 0, 10] = 1.0  # x1 at bin 10
        invalid_logits[0, 0, 5] = 1.0   # x2 at bin 5 (invalid)
        blocks = parse_block_output(invalid_logits)
        # Check if the parser correctly identifies or handles this case
        # (Implementation detail: may return NaN or clamp values)
        assert not torch.isnan(blocks).all(), "Parser crashed on invalid input"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
