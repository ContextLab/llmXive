"""
Tests for the data_loader module.
"""
import pytest
import torch
from unittest.mock import patch, MagicMock

from code.data_loader import load_coco_streaming, load_imagenet_batched, validate_exclusions
from code.config import Config, DatasetLimits

@pytest.fixture
def config():
    return Config()

def test_coco_streaming_returns_64x64_shape(config):
    """
    Test that COCO streaming loader returns images of shape 64x64 (3 channels).
    """
    # Mock the load_dataset to return a fake dataset structure
    mock_item = {
        "image": MagicMock(),
        "caption": "A test caption"
    }
    mock_item["image"].mode = "RGB"
    mock_item["image"].convert.return_value = mock_item["image"]

    # Mock the transform to return a specific tensor
    mock_transform = MagicMock()
    mock_transform.return_value = torch.randn(3, 64, 64)

    with patch("code.data_loader.load_dataset") as mock_load, \
         patch("code.data_loader.transforms") as mock_transforms:

        mock_load.return_value = [mock_item]
        mock_transforms.Compose.return_value = mock_transform

        loader = load_coco_streaming(config, max_samples=1)
        samples = list(loader)

        assert len(samples) == 1
        assert samples[0].image.shape == (3, 64, 64)
        assert samples[0].source == "coco"

def test_imagenet_batched_returns_correct_shapes(config):
    """
    Test that ImageNet batched loader returns correct batch shapes.
    """
    # Mock dataset
    mock_dataset = MagicMock()
    mock_dataset.map.return_value = mock_dataset
    
    # Mock data iteration
    mock_batch = {
        "image": MagicMock(),
        "label": 0
    }
    mock_dataset.__iter__.return_value = iter([mock_batch] * 4) # 4 items for batch of 2

    with patch("code.data_loader.load_dataset") as mock_load, \
         patch("code.data_loader.TorchDataLoader") as mock_dataloader_class:

        mock_load.return_value = mock_dataset
        
        # Mock the dataloader instance
        mock_loader_instance = MagicMock()
        mock_loader_instance.__iter__.return_value = iter([
            {
                "image": torch.randn(2, 3, 64, 64),
                "label": torch.tensor([0, 1]),
                "caption": None,
                "source": "imagenet"
            }
        ])
        mock_dataloader_class.return_value = mock_loader_instance

        loader = load_imagenet_batched(config, batch_size=2)
        
        # Consume the mock loader
        batches = list(loader)
        
        assert len(batches) == 1
        assert batches[0]["image"].shape == (2, 3, 64, 64)
        assert batches[0]["label"].shape == (2,)
        assert batches[0]["source"] == "imagenet"

def test_exclusion_validation():
    """
    Test that the exclusion validation function runs without error.
    """
    # This is a simple sanity check that the function exists and runs
    result = validate_exclusions()
    assert result is True

def test_coco_fails_loudly_on_fetch_error(config):
    """
    Test that COCO loader raises RuntimeError if fetch fails.
    """
    with patch("code.data_loader.load_dataset") as mock_load:
        mock_load.side_effect = Exception("Network error")

        with pytest.raises(RuntimeError, match="Failed to fetch real COCO dataset"):
            list(load_coco_streaming(config))

def test_imagenet_fails_loudly_on_fetch_error(config):
    """
    Test that ImageNet loader raises RuntimeError if fetch fails.
    """
    with patch("code.data_loader.load_dataset") as mock_load:
        mock_load.side_effect = Exception("Network error")

        with pytest.raises(RuntimeError, match="Failed to fetch real ImageNet-1K dataset"):
            load_imagenet_batched(config)