import logging
from typing import Iterator, List, Dict, Any, Optional
from datasets import load_dataset
import torch
from PIL import Image
import io

logger = logging.getLogger(__name__)

def load_imagenet_subset(
    split: str = "validation",
    streaming: bool = True,
    num_images: Optional[int] = None
) -> Iterator[Dict[str, Any]]:
    """
    Load ImageNet dataset using HuggingFace datasets.
    
    Args:
        split: Dataset split to load (default: "validation").
        streaming: Whether to use streaming mode (default: True).
        num_images: Maximum number of images to yield (default: None, all).
        
    Yields:
        Dictionary containing 'image' (PIL.Image) and 'label' (int).
    """
    logger.info(f"Loading ImageNet {split} split (streaming={streaming})...")
    
    try:
        # Load dataset with streaming
        dataset = load_dataset("imagenet-1k", split=split, streaming=streaming)
        
        count = 0
        for item in dataset:
            if num_images is not None and count >= num_images:
                break
            
            # Ensure image is loaded
            if 'image' in item and item['image'] is not None:
                yield item
                count += 1
            else:
                logger.warning(f"Skipping item {count} due to missing image")
                
    except Exception as e:
        logger.error(f"Failed to load ImageNet dataset: {e}")
        # Per requirements, we must fail loudly, not fall back to synthetic
        raise RuntimeError(f"ImageNet dataset loading failed: {e}")

def preprocess_image(image: Image.Image) -> torch.Tensor:
    """
    Preprocess a PIL image for model input.
    
    Args:
        image: PIL Image to preprocess.
        
    Returns:
        Tensor of shape (3, H, W) with values in [0, 1].
    """
    # Convert to RGB if necessary
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    # Resize to 256x256 (common for diffusion models)
    image = image.resize((256, 256), Image.Resampling.LANCZOS)
    
    # Convert to tensor
    import torch
    tensor = torch.from_numpy(np.array(image)).permute(2, 0, 1).float() / 255.0
    
    return tensor
