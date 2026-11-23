import logging
from typing import Iterator, List, Dict, Any, Optional
from datasets import load_dataset
import torch
from PIL import Image
import io

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_imagenet_subset(split: str = "validation", streaming: bool = True) -> Iterator[Dict[str, Any]]:
    """
    Loads a subset of the ImageNet dataset using the HuggingFace datasets library.
    CRITICAL: This loader MUST fail loudly if the real source is unreachable.
    """
    try:
        dataset = load_dataset("imagenet1k", split=split, streaming=streaming)
        return iter(dataset)
    except Exception as e:
        logger.error(f"Failed to load ImageNet dataset: {e}")
        raise RuntimeError(f"Failed to load ImageNet dataset: {e}")

def preprocess_image(image: Image.Image) -> torch.Tensor:
    """
    Preprocesses an image for the model.
    Converts PIL Image to torch.Tensor and normalizes.
    """
    # Convert to RGB if necessary
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    # Resize to 256x256 (common size for diffusion models)
    image = image.resize((256, 256))
    
    # Convert to tensor
    import numpy as np
    img_array = np.array(image).astype(np.float32) / 255.0
    img_tensor = torch.from_numpy(img_array).permute(2, 0, 1)
    
    # Normalize to [-1, 1]
    img_tensor = (img_tensor - 0.5) * 2.0
    
    return img_tensor
