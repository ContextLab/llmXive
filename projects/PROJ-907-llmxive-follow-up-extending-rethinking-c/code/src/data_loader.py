"""
Data loading utilities for ImageNet.
"""
import logging
from typing import Iterator, List, Dict, Any, Optional
from datasets import load_dataset
import torch
from PIL import Image
import io

logger = logging.getLogger(__name__)

def load_imagenet_subset(split: str = "validation", streaming: bool = True):
    """
    Fetch ImageNet subsets using datasets.load_dataset.
    
    Args:
        split: The split to load (e.g., "validation").
        streaming: Whether to stream the dataset.
        
    Returns:
        An iterable dataset object.
        
    Raises:
        Exception: If the real source is unreachable.
    """
    logger.info(f"Loading ImageNet subset: split={split}, streaming={streaming}")
    try:
        # Using the real dataset source as specified
        dataset = load_dataset("imagenetk", split=split, streaming=streaming)
        logger.info("Dataset loaded successfully.")
        return dataset
    except Exception as e:
        logger.error(f"Failed to load dataset from real source: {e}")
        # CRITICAL: Do NOT fall back to synthetic data. Raise the error.
        raise

def preprocess_image(image: Image.Image, size: int = 256) -> torch.Tensor:
    """
    Preprocess an image for model input.
    
    Args:
        image: The PIL image.
        size: The target size.
        
    Returns:
        A tensor of shape [3, size, size].
    """
    # Resize and convert to tensor
    image = image.resize((size, size))
    # Convert to tensor (0-255 -> 0-1)
    tensor = torch.from_numpy(np.array(image)).permute(2, 0, 1).float() / 255.0
    # Normalize if needed (depending on model requirements)
    # For now, return as is
    return tensor

# Import numpy here to avoid circular imports if any
import numpy as np
