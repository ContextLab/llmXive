import logging
from typing import Iterator, List, Dict, Any, Optional
from datasets import load_dataset
import torch
from PIL import Image
import io

logger = logging.getLogger(__name__)

def load_imagenet_subset(num_images: int, start_idx: int = 0) -> List[Dict[str, Any]]:
    """
    Fetches a subset of ImageNet-1k validation images using the HuggingFace datasets library.
    
    This function streams the dataset to avoid loading everything into memory.
    It strictly adheres to the "fail loud" policy: if the real source is unreachable,
    it raises an exception and does NOT fallback to synthetic data.
    
    Args:
        num_images: Number of images to retrieve.
        start_idx: Starting index in the validation split.
    
    Returns:
        A list of dictionaries containing 'image' (PIL Image) and 'label'.
    
    Raises:
        RuntimeError: If the dataset cannot be fetched or is unreachable.
    """
    logger.info(f"Attempting to load ImageNet-1k validation subset: indices {start_idx} to {start_idx + num_images}")
    
    try:
        # Load the dataset in streaming mode
        # This fetches real data from the HuggingFace Hub
        dataset = load_dataset("imagenet-1k", split="validation", streaming=True)
        
        # Iterate and collect the required subset
        images_data = []
        count = 0
        
        # We need to skip 'start_idx' items and take 'num_images'
        # Since it's a streaming dataset, we iterate through it
        iterator = iter(dataset)
        
        # Skip start_idx
        for _ in range(start_idx):
            try:
                next(iterator)
            except StopIteration:
                raise RuntimeError(f"Requested start_idx {start_idx} is beyond the dataset size.")
        
        # Collect num_images
        for item in iterator:
            if count >= num_images:
                break
            
            # The dataset item usually has 'image' (PIL) and 'label' (int)
            # Ensure the image is loaded
            img = item.get('image')
            label = item.get('label')
            
            if img is None:
                logger.warning(f"Skipping item at index {start_idx + count}: missing 'image' key.")
                continue
            
            images_data.append({
                'image': img,
                'label': label,
                'index': start_idx + count
            })
            count += 1
        
        if count < num_images:
            logger.warning(f"Requested {num_images} images but only found {count} available in the dataset.")
        
        logger.info(f"Successfully loaded {len(images_data)} images from ImageNet-1k.")
        return images_data

    except Exception as e:
        # CRITICAL: Do NOT fallback to synthetic data.
        # Raise the error to indicate the real source is unreachable.
        logger.error(f"CRITICAL: Failed to fetch real ImageNet data from HuggingFace Hub: {e}")
        raise RuntimeError(f"Failed to load real ImageNet data. The dataset source is unreachable. Error: {e}") from e
