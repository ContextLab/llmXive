"""
Unit tests for the VisionEncoder module.
"""

import pytest
import sys
import numpy as np
from pathlib import Path
import torch
from unittest.mock import patch, MagicMock

# Ensure src is in path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.vision_encoder import VisionEncoder, create_vision_encoder, SemanticEmbedding


class TestVisionEncoder:
    """Test suite for VisionEncoder."""

    def test_create_vision_encoder(self):
        """Test that create_vision_encoder returns a VisionEncoder instance."""
        encoder = create_vision_encoder()
        assert isinstance(encoder, VisionEncoder)
        assert encoder.device.type == "cpu"

    def test_encoder_device(self):
        """Test that the encoder is on CPU."""
        encoder = create_vision_encoder()
        assert encoder.device.type == "cpu"

    def test_embed_dim(self):
        """Test that the embedding dimension is correct."""
        encoder = create_vision_encoder()
        assert encoder.EMBED_DIM == 512

    def test_encode_frame_numpy(self):
        """Test encoding a single numpy frame."""
        encoder = create_vision_encoder()
        # Create a dummy frame (H, W, C)
        frame = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
        
        # Mock the forward method to avoid actual model loading and complex feature extraction logic
        # which might fail in a unit test environment without real weights or specific torchvision versions.
        with patch.object(encoder, 'forward', return_value=torch.zeros(1, encoder.EMBED_DIM)):
            embedding = encoder.encode_frame(frame)
        
        assert isinstance(embedding, SemanticEmbedding)
        assert embedding.vector.shape == (encoder.EMBED_DIM,)
        assert embedding.metadata["source"] == "mobilevit"

    def test_encode_frame_tensor(self):
        """Test encoding a single torch tensor frame."""
        encoder = create_vision_encoder()
        # Create a dummy tensor frame (C, H, W) in [0, 1]
        frame = torch.rand(3, 224, 224)
        
        with patch.object(encoder, 'forward', return_value=torch.zeros(1, encoder.EMBED_DIM)):
            embedding = encoder.encode_frame(frame)
        
        assert isinstance(embedding, SemanticEmbedding)
        assert embedding.vector.shape == (encoder.EMBED_DIM,)

    def test_encode_video_clip(self):
        """Test encoding a video clip (batch of frames)."""
        encoder = create_vision_encoder()
        # Create a dummy video clip (B, T, C, H, W)
        # B=1, T=5
        frames = torch.rand(1, 5, 3, 224, 224)
        
        with patch.object(encoder, 'forward', return_value=torch.zeros(1, 5, encoder.EMBED_DIM)):
            # Note: The forward method handles the reshaping internally if input is 5D
            # But our mock returns (B, T, E) which matches the expectation after reshaping
            # The actual forward implementation:
            # if 5D: reshape to (B*T, C, H, W) -> extract -> (B, T, E) -> mean -> (B, E)
            # So the mock should return (B*T, E) if we patch _extract_features, or (B, T, E) if we patch forward?
            # The forward method calls _extract_features.
            # Let's patch _extract_features to return (B*T, E)
            with patch.object(encoder, '_extract_features', return_value=torch.zeros(5, encoder.EMBED_DIM)):
                embedding = encoder.forward(frames)
        
        assert embedding.shape == (1, encoder.EMBED_DIM)

    def test_semantic_embedding_to_numpy(self):
        """Test SemanticEmbedding to_numpy method."""
        vec = torch.randn(512)
        emb = SemanticEmbedding(vec)
        arr = emb.to_numpy()
        
        assert isinstance(arr, np.ndarray)
        assert arr.shape == (512,)
        np.testing.assert_array_equal(arr, vec.numpy())

    def test_invalid_input_shape(self):
        """Test that invalid input shapes raise an error."""
        encoder = create_vision_encoder()
        # 1D tensor
        invalid_frame = torch.rand(10)
        
        with pytest.raises(ValueError):
            encoder.forward(invalid_frame)

    @pytest.mark.skip(reason="Requires real MobileViT weights and specific torchvision version")
    def test_end_to_end_real_model(self):
        """End-to-end test with real model (skipped in CI due to resource/model constraints)."""
        encoder = create_vision_encoder()
        frame = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
        embedding = encoder.encode_frame(frame)
        assert embedding.vector.shape == (512,)