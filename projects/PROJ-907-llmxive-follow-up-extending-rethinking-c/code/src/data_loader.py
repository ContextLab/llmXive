import logging
from typing import Iterator, List, Dict, Any, Optional
from datasets import load_dataset
import torch
from PIL import Image
import io

logger = logging.getLogger(__name__)

def load_imagenet_subset(split: str = "validation", streaming: bool = True) -> Iterator[Dict[str, Any]]:
    """
    Fetches ImageNet validation subset using the datasets library.
    CRITICAL: No synthetic fallback. Raises exception if source is unreachable.
    """
    try:
        # Use the canonical imagenet1k dataset
        ds = load_dataset("imagenet1k", split=split, streaming=streaming)
        return iter(ds)
    except Exception as e:
        logger.error(f"Failed to load ImageNet dataset: {e}")
        raise RuntimeError(f"Real data source unreachable: {e}")

def preprocess_image(pil_image: Image.Image) -> torch.Tensor:
    """
    Preprocesses a PIL image to a torch tensor.
    Resizes to 299x299 (standard for Inception, often used as baseline for diffusion too)
    and normalizes.
    """
    # Resize to 299x299 as per common baseline for FID and diffusion
    target_size = (299, 299)
    resized = pil_image.resize(target_size, Image.LANCZOS)
    
    # Convert to tensor [C, H, W] in range [0, 1]
    tensor = torch.from_numpy(resized).permute(2, 0, 1).float() / 255.0
    
    # Normalize to [-1, 1] if needed, or keep [0, 1]. 
    # Diffusion models often use [-1, 1]. Let's assume standard normalization.
    # For this task, we just return the tensor. The model loader handles specific normalization.
    # However, to be safe and standard:
    mean = torch.tensor([0.485, 0.456, 0.406]).view(3, 1, 1)
    std = torch.tensor([0.229, 0.224, 0.225]).view(3, 1, 1)
    tensor = (tensor - mean) / std
    
    return tensor
