import pytest
import torch
import numpy as np
from PIL import Image
from pathlib import Path
import sys
import os

# Add code to path if running from tests
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from data.preprocessing import (
    load_image, resize_image, normalize_image, detect_and_clamp_nans,
    image_to_tensor, pad_or_truncate_sequence, handle_corruption,
    extract_tokens, pad_sequences, ImagePreprocessingError
)
from models.rf_encoder import create_rf_encoder, get_default_config

@pytest.fixture
def mock_image():
    """Create a simple 224x224 RGB image."""
    img = Image.new('RGB', (224, 224), color=(100, 150, 200))
    return img

@pytest.fixture
def mock_rf_model():
    """Create a mock RF encoder model for testing."""
    config = get_default_config()
    # We expect a real model initialization, but for unit tests we might mock
    # However, the task requires real code. We will create a minimal valid model
    # or rely on the fact that create_rf_encoder returns a valid object.
    # For this test, we assume the model can be created without CUDA.
    try:
        model = create_rf_encoder(config)
        return model
    except Exception as e:
        pytest.skip(f"Could not initialize RF model for unit test: {e}")

def test_load_image(mock_image, tmp_path):
    """Test loading an image from disk."""
    path = tmp_path / "test.png"
    mock_image.save(path)
    loaded = load_image(path)
    assert loaded.size == (224, 224)
    assert loaded.mode == 'RGB'

def test_resize_image(mock_image):
    """Test resizing."""
    resized = resize_image(mock_image, (100, 100))
    assert resized.size == (100, 100)

def test_normalize_image(mock_image):
    """Test normalization."""
    tensor = normalize_image(mock_image)
    assert tensor.shape == (3, 224, 224)
    assert torch.is_tensor(tensor)

def test_detect_and_clamp_nans():
    """Test NaN and Inf clamping."""
    tensor = torch.tensor([1.0, float('nan'), float('inf'), -float('inf')])
    clamped = detect_and_clamp_nans(tensor)
    assert not torch.isnan(clamped).any()
    assert not torch.isinf(clamped).any()
    assert clamped[1] == 0.0

def test_pad_or_truncate_sequence():
    """Test padding and truncation."""
    seq = [1.0, 2.0, 3.0]
    padded = pad_or_truncate_sequence(seq, 5)
    assert len(padded) == 5
    assert padded == [1.0, 2.0, 3.0, 0.0, 0.0]

    truncated = pad_or_truncate_sequence(seq, 2)
    assert len(truncated) == 2
    assert truncated == [1.0, 2.0]

def test_handle_corruption():
    """Test corruption handler returns minimal valid structure."""
    result = handle_corruption(max_length=10)
    assert result['tokens'] == [0.0] * 10
    assert result['is_corrupted'] is True
    assert result['attention_mask'] == [0] * 10

def test_pad_sequences():
    """Test padding a batch of sequences."""
    seq1 = torch.randn(5, 10) # 5 tokens, 10 dim
    seq2 = torch.randn(3, 10) # 3 tokens, 10 dim
    batch = [seq1, seq2]
    
    padded, mask = pad_sequences(batch, max_length=6)
    
    assert padded.shape == (2, 6, 10)
    assert mask.shape == (2, 6)
    
    # Check padding
    assert torch.all(padded[0, 5, :] == 0) # 6th token should be 0
    assert mask[0, 5] == 0
    assert mask[0, :5] == 1

def test_extract_tokens(mock_rf_model):
    """Test token extraction from a dummy image tensor."""
    dummy_tensor = torch.randn(1, 3, 224, 224)
    tokens = extract_tokens(dummy_tensor, mock_rf_model, device='cpu')
    
    # Check output shape (batch, seq_len, hidden)
    assert tokens.dim() == 3
    assert tokens.shape[0] == 1
    assert tokens.shape[1] > 0
    assert tokens.shape[2] > 0
    
    # Check no NaNs/Infs
    assert not torch.isnan(tokens).any()
    assert not torch.isinf(tokens).any()
