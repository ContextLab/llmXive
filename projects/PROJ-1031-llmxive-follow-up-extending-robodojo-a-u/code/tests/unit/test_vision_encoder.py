"""
Unit tests for VisionEncoder logic.
"""
import pytest
import sys
import numpy as np
from pathlib import Path
import torch

# Ensure src is importable
src_path = Path(__file__).parent.parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from src.vision_encoder import VisionEncoder, create_vision_encoder


class TestVisionEncoder:
    """Tests for VisionEncoder class."""

    def test_encoder_initialization(self):
        """Verify VisionEncoder initializes with CPU-only mode."""
        encoder = VisionEncoder()
        assert encoder is not None
        # Check that device is CPU (as per requirement)
        assert encoder.device.type == 'cpu'

    def test_create_vision_encoder_factory(self):
        """Verify factory function returns an instance."""
        encoder = create_vision_encoder()
        assert isinstance(encoder, VisionEncoder)

    def test_embedding_generation_shape(self):
        """Verify embedding generation produces correct shape."""
        encoder = VisionEncoder()
        # Mock input: batch of 1 frame, 3 channels, 224x224
        mock_input = torch.randn(1, 3, 224, 224)

        # We expect a forward pass to produce an embedding
        # The exact shape depends on the MobileViT config, but it should be non-empty
        with torch.no_grad():
            embedding = encoder(mock_input)

        assert embedding.shape[0] == 1
        assert embedding.dim() > 1
