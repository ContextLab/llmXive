import logging
from typing import Iterator, List, Dict, Any, Optional
from datasets import load_dataset
import torch
from PIL import Image
import io

logger = logging.getLogger(__name__)

def load_imagenet_subset(
    dataset_name: str = "imagenet1k",
    split: str = "validation",
    streaming: bool = True
) -> Iterator[Dict[str, Any]]:
    """
    Load ImageNet subset using HuggingFace datasets.
    
    Args:
        dataset_name: Name of the dataset (e.g., "imagenet1k")
        split: Dataset split (e.g., "validation")
        streaming: Whether to stream the dataset
    
    Returns:
        Iterator of dataset items
    """
    try:
        dataset = load_dataset(dataset_name, split=split, streaming=streaming)
        logger.info(f"Successfully loaded dataset: {dataset_name}, split: {split}")
        return iter(dataset)
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        raise e

def preprocess_image(image: Image.Image) -> torch.Tensor:
    """
    Preprocess an image for model input.
    
    Args:
        image: PIL Image
    
    Returns:
        torch.Tensor: Preprocessed image tensor
    """
    # Convert to RGB if necessary
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    # Resize to 256x256 (common for diffusion models)
    image = image.resize((256, 256))
    
    # Convert to tensor and normalize
    # Assuming model expects values in [-1, 1]
    tensor = torch.from_numpy(np.array(image)).permute(2, 0, 1).float() / 255.0
    tensor = (tensor - 0.5) * 2.0
    return tensor
