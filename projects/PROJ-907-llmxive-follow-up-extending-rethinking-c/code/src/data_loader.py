import logging
from typing import Iterator, List, Dict, Any, Optional
from datasets import load_dataset
import torch
from PIL import Image
import io
import numpy as np

logger = logging.getLogger(__name__)

def load_imagenet_subset(split: str = "validation", streaming: bool = True, shuffle: bool = False) -> Iterator[Dict[str, Any]]:
    """
    Loads ImageNet-1k subset using the HuggingFace datasets library.
    
    CRITICAL (T035): This loader MUST fail loudly if the real source is unreachable.
    No synthetic fallback is allowed.
    
    Args:
        split: The dataset split to load (default: "validation").
        streaming: If True, streams data without downloading the full dataset.
        shuffle: If True, shuffles the dataset.
    
    Returns:
        An iterator yielding dictionaries with 'image' and 'label' keys.
    
    Raises:
        Exception: If the dataset cannot be loaded (e.g., network error, missing package).
    """
    logger.info(f"Loading ImageNet-1k dataset: split={split}, streaming={streaming}")
    
    try:
        # Real source: HuggingFace datasets
        # If this fails, it raises an exception (network error, auth error, etc.)
        # We do NOT catch and fallback to synthetic data.
        dataset = load_dataset(
            "imagenet-1k", 
            split=split, 
            streaming=streaming,
            trust_remote_code=True
        )
        
        if shuffle:
            dataset = dataset.shuffle(seed=42)
        
        logger.info("ImageNet-1k dataset loaded successfully.")
        return iter(dataset)
        
    except Exception as e:
        logger.error(f"Failed to load ImageNet-1k dataset: {e}")
        # Re-raise to ensure the execution fails loudly
        raise RuntimeError(f"Data source unavailable: {e}") from e

def preprocess_image(image: Image.Image, size: int = 256) -> torch.Tensor:
    """
    Preprocesses a PIL Image to a tensor.
    
    Args:
        image: PIL Image.
        size: Target size for resizing.
    
    Returns:
        Tensor of shape (3, H, W) with values in [0, 1].
    """
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    image = image.resize((size, size))
    img_array = np.array(image).astype(np.float32) / 255.0
    tensor = torch.from_numpy(img_array).permute(2, 0, 1)
    return tensor
