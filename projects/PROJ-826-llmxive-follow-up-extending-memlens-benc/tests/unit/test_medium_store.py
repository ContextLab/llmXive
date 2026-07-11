"""
Unit tests for MediumStore.
"""

import os
import json
import tempfile
import pytest
from unittest.mock import patch, MagicMock

import torch
from PIL import Image
import numpy as np

# Add project root to path if running standalone
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from stores.medium_store import MediumStore


@pytest.fixture
def sample_data_path(tmp_path):
    """Create a temporary directory with sample data."""
    data_dir = tmp_path / "raw"
    data_dir.mkdir()
    
    # Create a dummy image
    img_path = data_dir / "test_image.jpg"
    img = Image.new('RGB', (224, 224), color='red')
    img.save(img_path)
    
    # Create sample JSONL data
    jsonl_path = data_dir / "mem_lens_filtered.jsonl"
    with open(jsonl_path, 'w') as f:
        f.write(json.dumps({
            "id": "test-001",
            "summary": "A red square on a white background.",
            "image_path": str(img_path),
            "metadata": {"session": "test"}
        }) + "\n")
        f.write(json.dumps({
            "id": "test-002",
            "summary": "No image here.",
            "image_path": None,
            "metadata": {}
        }) + "\n")
    
    return str(data_dir)


@pytest.fixture
def mock_clip_model():
    """Mock the CLIP model to avoid heavy downloads during tests."""
    with patch('stores.medium_store.CLIPModel.from_pretrained') as mock_model, \
         patch('stores.medium_store.CLIPProcessor.from_pretrained') as mock_proc:
         
         mock_model.return_value.eval.return_value.get_image_features.return_value = torch.randn(1, 512)
         mock_model.return_value.parameters.return_value = [] # No params to freeze
         mock_model.return_value.to.return_value = mock_model.return_value
         
         mock_proc.return_value.return_value = {"pixel_values": torch.randn(1, 3, 224, 224)}
         
         yield mock_model


def test_medium_store_init(mock_clip_model):
    """Test initialization of MediumStore."""
    store = MediumStore()
    assert store.model_name == "openai/clip-vit-base-patch32"
    assert store.index == []
    assert store.faiss_index is None


def test_load_data(mock_clip_model, sample_data_path):
    """Test loading data and computing embeddings."""
    store = MediumStore()
    store.load_data(sample_data_path)
    
    assert len(store.index) == 2
    
    # Check first item has embedding
    item1 = next(i for i in store.index if i["id"] == "test-001")
    assert item1["summary"] == "A red square on a white background."
    assert item1["image_embedding"] is not None
    assert len(item1["image_embedding"]) == 512 # CLIP base dimension
    
    # Check second item has no embedding
    item2 = next(i for i in store.index if i["id"] == "test-002")
    assert item2["image_embedding"] is None


def test_build_index(mock_clip_model, sample_data_path):
    """Test building FAISS index."""
    store = MediumStore()
    store.load_data(sample_data_path)
    store.build_index()
    
    assert store.faiss_index is not None
    assert len(store.valid_ids) == 1 # Only one item with image
    assert "test-001" in store.valid_ids


def test_save_and_load(mock_clip_model, sample_data_path, tmp_path):
    """Test saving and loading the store."""
    store = MediumStore()
    store.load_data(sample_data_path)
    store.build_index()
    
    save_path = str(tmp_path / "store.pkl")
    store.save(save_path)
    
    assert os.path.exists(save_path)
    
    loaded_store = MediumStore.load(save_path)
    assert len(loaded_store.index) == len(store.index)
    assert loaded_store.valid_ids == store.valid_ids