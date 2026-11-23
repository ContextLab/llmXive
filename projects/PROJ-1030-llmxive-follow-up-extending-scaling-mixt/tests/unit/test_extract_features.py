"""
Unit tests for extract_features.py.

These tests verify the extraction logic, data loading, and file saving
without requiring a full GPU or large video dataset.
"""
import os
import sys
import json
import tempfile
import numpy as np
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import torch
from torch import nn

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from extract_features import (
    ExtractionStats,
    ExtractionResult,
    get_memory_usage_mb,
    extract_activations,
    save_features
)

class MockLayer(nn.Module):
    """Mock layer to simulate MoE behavior."""
    def __init__(self):
        super().__init__()
        self.expert_weights = torch.tensor([0.1, 0.9, 0.0]) # 3 experts, 2 active

    def forward(self, x):
        return x

class MockModel(nn.Module):
    """Mock model for testing hooks."""
    def __init__(self):
        super().__init__()
        self.layer = MockLayer()

    def forward(self, x):
        return self.layer(x)

def test_extraction_result_creation():
    """Test that ExtractionResult is created correctly."""
    latent = np.random.rand(768)
    mask = np.array([1, 0, 1])
    result = ExtractionResult(
        clip_id="test_001",
        latent_vector=latent,
        expert_mask=mask,
        metadata={"test": True}
    )
    assert result.clip_id == "test_001"
    assert result.latent_vector.shape == (768,)
    assert np.array_equal(result.expert_mask, mask)

def test_extract_activations_with_mock_model():
    """Test the hook mechanism with a mock model."""
    model = MockModel()
    clip_id = "mock_clip"
    video_tensor = torch.randn(1, 10, 3, 32, 32)
    
    result = extract_activations(model, clip_id, video_tensor, "cpu")
    
    assert result is not None
    assert result.clip_id == clip_id
    assert result.latent_vector is not None
    assert result.expert_mask is not None
    # Verify mask has expected size (3 experts)
    assert result.expert_mask.shape[0] == 3

def test_save_features(tmp_path):
    """Test saving features to .npy and .json."""
    # Create mock results
    results = [
        ExtractionResult(
            clip_id="c1",
            latent_vector=np.random.rand(10),
            expert_mask=np.array([1, 0]),
            metadata={"id": "c1"}
        ),
        ExtractionResult(
            clip_id="c2",
            latent_vector=np.random.rand(10),
            expert_mask=np.array([0, 1]),
            metadata={"id": "c2"}
        )
    ]
    
    npy_path = tmp_path / "features.npy"
    json_path = tmp_path / "features_metadata.json"
    
    save_features(results, str(npy_path), str(json_path))
    
    # Verify files exist
    assert npy_path.exists()
    assert json_path.exists()
    
    # Verify content
    data = np.load(npy_path, allow_pickle=True)
    assert "latents" in data.files
    assert "masks" in data.files
    assert "clip_ids" in data.files
    assert data["latents"].shape == (2, 10)
    assert data["masks"].shape == (2, 2)
    
    with open(json_path) as f:
        meta = json.load(f)
    assert meta["total_samples"] == 2
    assert len(meta["samples"]) == 2

def test_empty_results_fails():
    """Test that saving empty results raises an error."""
    with pytest.raises(Exception):
        save_features([], "dummy.npy", "dummy.json")

def test_memory_usage_reporting():
    """Test that memory usage function returns a number."""
    mem = get_memory_usage_mb()
    assert isinstance(mem, float)
    assert mem >= 0