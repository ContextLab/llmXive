import pytest
import torch
from data_loader import COCOStreamingDataset, get_dataloader

def test_data_loader_streaming_returns_64x64_shape():
    """
    Verify that the COCO streaming dataset returns images of shape (3, 64, 64).
    """
    # Use a small limit for fast testing
    dataset = COCOStreamingDataset(split="train", resolution=64, limit=10)
    dataloader = get_dataloader(dataset, batch_size=2, shuffle=False)
    
    for batch in dataloader:
        images = batch['pixel_values']
        assert images.shape[1] == 3, f"Expected 3 channels, got {images.shape[1]}"
        assert images.shape[2] == 64, f"Expected height 64, got {images.shape[2]}"
        assert images.shape[3] == 64, f"Expected width 64, got {images.shape[3]}"
        break # Only need to check one batch
