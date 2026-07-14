"""
Data augmentation transforms for material strength prediction.

Implements FR-003: Data augmentation transforms (random rotation, flip, brightness).
These transforms are applied on-the-fly during training to improve model generalization.
"""

import torch
import torchvision.transforms as transforms
from typing import Dict, Any, Optional, Union
import random

# Configuration defaults matching typical CNN training practices
DEFAULT_ROTATION_DEGREES = 15
DEFAULT_FLIP_PROB = 0.5
DEFAULT_BRIGHTNESS_FACTOR = 0.2
DEFAULT_CONTRAST_FACTOR = 0.2
DEFAULT_SATURATION_FACTOR = 0.2
DEFAULT_HUE_FACTOR = 0.1
DEFAULT_GAUSSIAN_NOISE_STD = 0.01
DEFAULT_GAUSSIAN_MEAN = 0.0

def get_train_augmentations(
    rotation_degrees: float = DEFAULT_ROTATION_DEGREES,
    flip_probability: float = DEFAULT_FLIP_PROB,
    brightness_factor: float = DEFAULT_BRIGHTNESS_FACTOR,
    contrast_factor: float = DEFAULT_CONTRAST_FACTOR,
    saturation_factor: float = DEFAULT_SATURATION_FACTOR,
    hue_factor: float = DEFAULT_HUE_FACTOR,
    gaussian_noise_std: float = DEFAULT_GAUSSIAN_NOISE_STD,
    target_size: tuple = (224, 224)
) -> transforms.Compose:
    """
    Constructs a Compose of augmentation transforms for training data.

    Args:
        rotation_degrees: Max degrees for random rotation.
        flip_probability: Probability of horizontal flip.
        brightness_factor: Brightness jitter factor.
        contrast_factor: Contrast jitter factor.
        saturation_factor: Saturation jitter factor.
        hue_factor: Hue jitter factor.
        gaussian_noise_std: Standard deviation for Gaussian noise.
        target_size: Target (height, width) for resizing.

    Returns:
        A torchvision.transforms.Compose object ready for use in a DataLoader.
    """
    transforms_list = [
        # Random rotation (using PIL interpolation if input is PIL, or nearest for tensors)
        # Since we handle PIL images before conversion or tensor images,
        # we use RandomRotation which handles PIL well.
        transforms.RandomRotation(degrees=rotation_degrees),
        
        # Random Horizontal Flip
        transforms.RandomHorizontalFlip(p=flip_probability),
        
        # Random Vertical Flip (optional but good for microstructures)
        transforms.RandomVerticalFlip(p=flip_probability),
        
        # Color jitter for brightness, contrast, saturation, hue
        transforms.ColorJitter(
            brightness=brightness_factor,
            contrast=contrast_factor,
            saturation=saturation_factor,
            hue=hue_factor
        ),
        
        # Resize to target size (224x224)
        # Using bilinear interpolation for smooth resizing
        transforms.Resize(target_size, interpolation=transforms.InterpolationMode.BILINEAR),
        
        # Random Erasing to simulate occlusions or defects
        transforms.RandomErasing(p=0.2, scale=(0.02, 0.33), ratio=(0.3, 3.3)),
    ]

    # Convert to tensor and normalize (standard ImageNet stats or 0-1 scale)
    # Since this is a custom dataset, we normalize to mean=0.5, std=0.5 or ImageNet stats
    # assuming the data loader handles the raw conversion. 
    # We append standard normalization here.
    transforms_list.append(transforms.ToTensor())
    
    # Normalize using standard ImageNet statistics (common practice for transfer learning)
    # If using a custom backbone trained on ImageNet, these are appropriate.
    # Otherwise, 0.5/0.5 is a safe default for 0-1 images.
    transforms_list.append(transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    ))

    # Optional: Add Gaussian noise if requested (applied on tensor)
    if gaussian_noise_std > 0:
        # Custom transform for Gaussian noise
        transforms_list.append(AddGaussianNoise(mean=DEFAULT_GAUSSIAN_MEAN, std=gaussian_noise_std))

    return transforms.Compose(transforms_list)


def get_val_augmentations(target_size: tuple = (224, 224)) -> transforms.Compose:
    """
    Constructs transforms for validation/test data (no augmentation).
    
    Args:
        target_size: Target (height, width).
        
    Returns:
        A Compose of deterministic transforms.
    """
    return transforms.Compose([
        transforms.Resize(target_size, interpolation=transforms.InterpolationMode.BILINEAR),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        ),
    ])


class AddGaussianNoise:
    """
    Custom transform to add Gaussian noise to a tensor.
    """
    def __init__(self, mean: float = 0.0, std: float = 0.1):
        self.mean = mean
        self.std = std

    def __call__(self, tensor: torch.Tensor) -> torch.Tensor:
        """
        Args:
            tensor (Tensor): Tensor image of size (C, H, W) to add noise to.
        
        Returns:
            Tensor: Noisy tensor image.
        """
        noise = torch.randn(tensor.size()) * self.std + self.mean
        return tensor + noise

    def __repr__(self):
        return self.__class__.__name__ + '(mean={0}, std={1})'.format(self.mean, self.std)


# Main entry point for standalone testing
def main():
    """
    Standalone test to verify augmentation logic.
    Generates a dummy image, applies transforms, and prints shape/stats.
    """
    import numpy as np
    import cv2
    from pathlib import Path
    import sys
    
    # Add parent to path for imports if running as script
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    # Create a dummy synthetic image (simulating a microstructure)
    # 224x224 grayscale or RGB
    dummy_img = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
    
    # Convert to PIL Image for transforms
    from PIL import Image
    pil_img = Image.fromarray(dummy_img)
    
    # Get train transforms
    train_transforms = get_train_augmentations()
    
    # Apply transforms
    try:
        augmented_tensor = train_transforms(pil_img)
        print(f"✅ Augmentation successful.")
        print(f"   Input shape: {dummy_img.shape}")
        print(f"   Output shape: {augmented_tensor.shape}")
        print(f"   Output dtype: {augmented_tensor.dtype}")
        print(f"   Output range: [{augmented_tensor.min():.3f}, {augmented_tensor.max():.3f}]")
        
        # Verify normalization roughly (should be around 0 with std 1)
        print(f"   Output mean: {augmented_tensor.mean():.3f}")
        print(f"   Output std: {augmented_tensor.std():.3f}")
        
        return 0
    except Exception as e:
        print(f"❌ Augmentation failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())