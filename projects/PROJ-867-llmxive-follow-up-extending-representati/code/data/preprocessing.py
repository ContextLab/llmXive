"""
Preprocessing module for llmXive structured text generation pipeline.

Provides image loading, resizing, normalization, and tensor conversion
utilities shared across all user stories.
"""

import os
import logging
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List, Union

import numpy as np
from PIL import Image
import torch
from torch.utils.data import Dataset, DataLoader

from config import get_config_dict, ensure_dirs
from data.loaders import load_publaynet

# Configure logging
logger = logging.getLogger(__name__)

# Constants
DEFAULT_IMAGE_SIZE = (224, 224)
DEFAULT_MEAN = [0.485, 0.456, 0.406]
DEFAULT_STD = [0.229, 0.224, 0.225]

class ImagePreprocessingError(Exception):
    """Custom exception for image preprocessing failures."""
    pass

def load_image(image_path: Union[str, Path], mode: str = "RGB") -> Image.Image:
    """
    Load an image from disk.
    
    Args:
        image_path: Path to the image file.
        mode: PIL image mode ('RGB', 'L', etc.).
        
    Returns:
        Loaded PIL Image.
        
    Raises:
        ImagePreprocessingError: If image cannot be loaded or is corrupted.
    """
    try:
        img = Image.open(image_path)
        # Ensure correct mode
        if img.mode != mode:
            img = img.convert(mode)
        return img
    except Exception as e:
        raise ImagePreprocessingError(f"Failed to load image {image_path}: {e}")

def resize_image(
    image: Image.Image, 
    size: Tuple[int, int] = DEFAULT_IMAGE_SIZE, 
    resample: int = Image.BILINEAR
) -> Image.Image:
    """
    Resize image to specified dimensions.
    
    Args:
        image: Input PIL Image.
        size: Target (width, height).
        resample: Resampling filter.
        
    Returns:
        Resized PIL Image.
    """
    return image.resize(size, resample)

def normalize_image(
    image: Image.Image,
    mean: List[float] = DEFAULT_MEAN,
    std: List[float] = DEFAULT_STD
) -> np.ndarray:
    """
    Normalize image pixel values to [0, 1] and apply standard normalization.
    
    Args:
        image: Input PIL Image.
        mean: Mean values for each channel.
        std: Standard deviation values for each channel.
        
    Returns:
        Normalized numpy array of shape (C, H, W).
    """
    # Convert to numpy array
    img_array = np.array(image).astype(np.float32)
    
    # Normalize to [0, 1]
    img_array /= 255.0
    
    # Ensure 3 channels
    if len(img_array.shape) == 2:
        img_array = np.stack([img_array] * 3, axis=-1)
    
    # Transpose to (C, H, W)
    img_array = np.transpose(img_array, (2, 0, 1))
    
    # Apply normalization
    for c, m, s in zip(range(len(mean)), mean, std):
        img_array[c] = (img_array[c] - m) / s
    
    return img_array

def detect_and_clamp_nans(tensor: torch.Tensor) -> torch.Tensor:
    """
    Detect NaN values in a tensor and clamp them to 0.
    
    Args:
        tensor: Input tensor.
        
    Returns:
        Tensor with NaNs replaced by 0.
    """
    if torch.isnan(tensor).any():
        logger.warning("NaN values detected in tensor, clamping to 0.")
        tensor = torch.nan_to_num(tensor, nan=0.0, posinf=1e6, neginf=-1e6)
    return tensor

def image_to_tensor(
    image: Image.Image,
    size: Tuple[int, int] = DEFAULT_IMAGE_SIZE,
    mean: List[float] = DEFAULT_MEAN,
    std: List[float] = DEFAULT_STD,
    clamp_nans: bool = True
) -> torch.Tensor:
    """
    Convert PIL Image to normalized torch tensor.
    
    Args:
        image: Input PIL Image.
        size: Target size for resizing.
        mean: Mean for normalization.
        std: Std for normalization.
        clamp_nans: Whether to clamp NaN values.
        
    Returns:
        Normalized torch tensor of shape (1, C, H, W).
    """
    # Resize
    resized = resize_image(image, size)
    
    # Normalize
    normalized = normalize_image(resized, mean, std)
    
    # Convert to tensor
    tensor = torch.from_numpy(normalized).unsqueeze(0)
    
    # Clamp NaNs if requested
    if clamp_nans:
        tensor = detect_and_clamp_nans(tensor)
    
    return tensor

def load_and_preprocess_image(
    image_path: Union[str, Path],
    size: Tuple[int, int] = DEFAULT_IMAGE_SIZE,
    mean: List[float] = DEFAULT_MEAN,
    std: List[float] = DEFAULT_STD
) -> torch.Tensor:
    """
    Load, resize, and normalize an image in one step.
    
    Args:
        image_path: Path to image file.
        size: Target size.
        mean: Mean for normalization.
        std: Std for normalization.
        
    Returns:
        Normalized torch tensor.
    """
    image = load_image(image_path)
    return image_to_tensor(image, size, mean, std)

class PubLayNetPreprocessedDataset(Dataset):
    """
    Dataset wrapper for PubLayNet that loads and preprocesses images.
    
    This dataset uses the real PubLayNet data from HuggingFace and applies
    on-the-fly preprocessing (resize, normalize) to avoid memory issues.
    """
    
    def __init__(
        self,
        split: str = "train",
        size: Tuple[int, int] = DEFAULT_IMAGE_SIZE,
        mean: List[float] = DEFAULT_MEAN,
        std: List[float] = DEFAULT_STD,
        max_samples: Optional[int] = None
    ):
        """
        Initialize the dataset.
        
        Args:
            split: Dataset split ('train', 'validation', 'test').
            size: Target image size.
            mean: Normalization mean.
            std: Normalization std.
            max_samples: Maximum number of samples to load (for testing).
        """
        self.split = split
        self.size = size
        self.mean = mean
        self.std = std
        self.max_samples = max_samples
        
        # Load the dataset
        logger.info(f"Loading PubLayNet split '{split}'...")
        self.dataset = load_publaynet()
        
        # Select split
        if split not in self.dataset:
            raise ValueError(f"Split '{split}' not found. Available: {list(self.dataset.keys())}")
        
        self.data = self.dataset[split]
        
        # Limit samples if requested
        if max_samples is not None and len(self.data) > max_samples:
            logger.info(f"Limiting to {max_samples} samples.")
            self.data = self.data.select(range(max_samples))
        
        logger.info(f"Dataset loaded: {len(self.data)} samples.")
    
    def __len__(self) -> int:
        return len(self.data)
    
    def __getitem__(self, idx: int) -> Dict[str, Any]:
        """
        Get a preprocessed sample.
        
        Args:
            idx: Sample index.
            
        Returns:
            Dictionary with 'image' tensor and 'annotation' dict.
        """
        sample = self.data[idx]
        
        # Load and preprocess image
        image_path = sample['image_path']
        if not os.path.exists(image_path):
            # Fallback: try to reconstruct path from image_id
            image_id = sample.get('image_id', f'image_{idx}')
            # In real usage, the loader should have downloaded images
            # For now, we raise an error
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        try:
            image_tensor = load_and_preprocess_image(
                image_path, self.size, self.mean, self.std
            )
        except Exception as e:
            logger.warning(f"Failed to process image {image_path}: {e}. Skipping.")
            # Return a minimal valid structure for corrupted images
            image_tensor = torch.zeros((1, 3, self.size[1], self.size[0]))
        
        return {
            'image': image_tensor,
            'annotation': sample['annotation'],
            'image_id': sample.get('image_id', idx)
        }

def create_preprocessing_dataloader(
    split: str = "train",
    batch_size: int = 8,
    num_workers: int = 0,
    size: Tuple[int, int] = DEFAULT_IMAGE_SIZE,
    max_samples: Optional[int] = None
) -> DataLoader:
    """
    Create a DataLoader for preprocessed PubLayNet data.
    
    Args:
        split: Dataset split.
        batch_size: Batch size.
        num_workers: Number of worker processes.
        size: Image size.
        max_samples: Maximum samples to load.
        
    Returns:
        DataLoader instance.
    """
    dataset = PubLayNetPreprocessedDataset(
        split=split,
        size=size,
        max_samples=max_samples
    )
    
    return DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=(split == "train"),
        num_workers=num_workers,
        pin_memory=False  # Disable for CPU-only compatibility
    )

def main():
    """
    Main function to demonstrate preprocessing pipeline.
    
    This script loads a small subset of PubLayNet, preprocesses images,
    and saves a sample of preprocessed tensors to disk.
    """
    # Ensure output directory exists
    ensure_dirs()
    output_dir = Path("data/preprocessed")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create dataloader with small sample for demo
    logger.info("Creating dataloader...")
    dataloader = create_preprocessing_dataloader(
        split="validation",
        batch_size=4,
        num_workers=0,
        max_samples=10  # Small sample for demo
    )
    
    # Process and save a few samples
    sample_count = 0
    for batch_idx, batch in enumerate(dataloader):
        images = batch['image']
        annotations = batch['annotation']
        image_ids = batch['image_id']
        
        logger.info(f"Batch {batch_idx}: {images.shape[0]} samples")
        
        for i, (img, ann, img_id) in enumerate(zip(images, annotations, image_ids)):
            # Save tensor to disk
            output_path = output_dir / f"preprocessed_{img_id}_{sample_count}.pt"
            torch.save({
                'image': img,
                'annotation': ann,
                'image_id': img_id
            }, output_path)
            
            sample_count += 1
            if sample_count >= 5:  # Save 5 samples
                break
        
        if sample_count >= 5:
            break
    
    logger.info(f"Saved {sample_count} preprocessed samples to {output_dir}")
    
    # Also save a summary
    summary = {
        'total_samples_processed': sample_count,
        'image_size': DEFAULT_IMAGE_SIZE,
        'mean': DEFAULT_MEAN,
        'std': DEFAULT_STD
    }
    
    summary_path = output_dir / "preprocessing_summary.json"
    import json
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Summary saved to {summary_path}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Preprocess PubLayNet images")
    parser.add_argument("--split", type=str, default="validation",
                      choices=["train", "validation", "test"],
                      help="Dataset split to process")
    parser.add_argument("--max-samples", type=int, default=10,
                      help="Maximum number of samples to process")
    parser.add_argument("--batch-size", type=int, default=4,
                      help="Batch size for dataloader")
    
    args = parser.parse_args()
    
    # Override defaults
    import sys
    sys.argv = [sys.argv[0]]  # Clear args for main()
    
    # Run with custom args
    # Temporarily patch main to accept args
    original_main = main
    
    def main_with_args():
        global DEFAULT_IMAGE_SIZE, DEFAULT_MEAN, DEFAULT_STD
        # Create dataloader with custom args
        ensure_dirs()
        output_dir = Path("data/preprocessed")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Processing split '{args.split}' with max {args.max_samples} samples...")
        dataloader = create_preprocessing_dataloader(
            split=args.split,
            batch_size=args.batch_size,
            num_workers=0,
            max_samples=args.max_samples
        )
        
        sample_count = 0
        for batch_idx, batch in enumerate(dataloader):
            images = batch['image']
            annotations = batch['annotation']
            image_ids = batch['image_id']
            
            logger.info(f"Batch {batch_idx}: {images.shape[0]} samples")
            
            for i, (img, ann, img_id) in enumerate(zip(images, annotations, image_ids)):
                output_path = output_dir / f"preprocessed_{img_id}_{sample_count}.pt"
                torch.save({
                    'image': img,
                    'annotation': ann,
                    'image_id': img_id
                }, output_path)
                
                sample_count += 1
                if sample_count >= args.max_samples:
                    break
            
            if sample_count >= args.max_samples:
                break
        
        logger.info(f"Saved {sample_count} preprocessed samples to {output_dir}")
        
        summary = {
            'total_samples_processed': sample_count,
            'image_size': DEFAULT_IMAGE_SIZE,
            'mean': DEFAULT_MEAN,
            'std': DEFAULT_STD,
            'split': args.split
        }
        
        summary_path = output_dir / "preprocessing_summary.json"
        import json
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"Summary saved to {summary_path}")
    
    main_with_args()
