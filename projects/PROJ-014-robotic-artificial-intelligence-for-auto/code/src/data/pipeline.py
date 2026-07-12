"""
Data pipeline for sensory modality preprocessing.
Implements RGB preprocessing: center-crop, normalization, and fixed spatial resolution.
"""
import numpy as np
from typing import Tuple, Optional, Union
from dataclasses import dataclass
import logging

from src.utils.config import get_hyperparameter

logger = logging.getLogger(__name__)


@dataclass
class RGBPreprocessingConfig:
    """Configuration for RGB preprocessing pipeline."""
    target_height: int = 84
    target_width: int = 84
    center_crop_size: Optional[int] = None  # If None, calculated to fit aspect ratio
    normalize: bool = True
    mean: Tuple[float, float, float] = (0.485, 0.456, 0.406)
    std: Tuple[float, float, float] = (0.229, 0.224, 0.225)


class RGBPreprocessor:
    """
    Preprocesses raw RGB images for neural network input.
    Operations: Center crop, resize to fixed resolution, normalize.
    """

    def __init__(self, config: Optional[RGBPreprocessingConfig] = None):
        self.config = config or RGBPreprocessingConfig()
        self._validate_config()

    def _validate_config(self) -> None:
        """Validate configuration parameters."""
        if self.config.target_height <= 0 or self.config.target_width <= 0:
            raise ValueError("Target dimensions must be positive")
        if self.config.center_crop_size is not None and self.config.center_crop_size <= 0:
            raise ValueError("Center crop size must be positive")

    def _center_crop(self, image: np.ndarray) -> np.ndarray:
        """
        Perform center crop on the image.
        
        Args:
            image: Input image array of shape (H, W, C) or (H, W)
            
        Returns:
            Cropped image array
        """
        if image.ndim == 2:
            # Grayscale to RGB if needed (though typically RGB is 3 channels)
            image = np.stack([image] * 3, axis=-1)
            
        h, w = image.shape[:2]
        
        # Determine crop dimensions
        if self.config.center_crop_size:
            crop_h = min(self.config.center_crop_size, h)
            crop_w = min(self.config.center_crop_size, w)
        else:
            # Default: crop to the smaller dimension to maintain aspect ratio
            crop_size = min(h, w)
            crop_h = crop_size
            crop_w = crop_size
        
        # Calculate start indices for center crop
        start_h = (h - crop_h) // 2
        start_w = (w - crop_w) // 2
        
        cropped = image[start_h:start_h + crop_h, start_w:start_w + crop_w]
        return cropped

    def _resize(self, image: np.ndarray) -> np.ndarray:
        """
        Resize image to target resolution using nearest neighbor or linear interpolation.
        Uses numpy for CPU-optimized resizing (no OpenCV dependency for this specific step
        to keep it lightweight, though OpenCV could be used if available).
        
        Args:
            image: Input image array
            
        Returns:
            Resized image array of shape (target_height, target_width, channels)
        """
        target_h = self.config.target_height
        target_w = self.config.target_width
        
        if image.shape[:2] == (target_h, target_w):
            return image
        
        # Simple resize implementation using numpy
        # For production, consider using cv2.resize or PIL for better quality
        h, w = image.shape[:2]
        
        # Calculate scaling factors
        scale_y = target_h / h
        scale_x = target_w / w
        
        # Create output array
        if image.ndim == 2:
            result = np.zeros((target_h, target_w), dtype=image.dtype)
        else:
            channels = image.shape[2]
            result = np.zeros((target_h, target_w, channels), dtype=image.dtype)
        
        # Map coordinates
        for y in range(target_h):
            src_y = int(y / scale_y)
            for x in range(target_w):
                src_x = int(x / scale_x)
                if image.ndim == 2:
                    result[y, x] = image[src_y, src_x]
                else:
                    result[y, x] = image[src_y, src_x]
        
        return result

    def _normalize_image(self, image: np.ndarray) -> np.ndarray:
        """
        Normalize image using standard ImageNet statistics.
        
        Args:
            image: Input image array (float32, range 0-255 or 0-1)
            
        Returns:
            Normalized image array
        """
        if image.dtype != np.float32:
            image = image.astype(np.float32)
        
        # Ensure range is 0-255 before normalization if it isn't already
        if image.max() > 1.0:
            image = image / 255.0
        
        # Normalize channel-wise
        mean = np.array(self.config.mean, dtype=np.float32)
        std = np.array(self.config.std, dtype=np.float32)
        
        # Expand dimensions for broadcasting
        if image.ndim == 2:
            # Grayscale case
            mean = mean[0]
            std = std[0]
            normalized = (image - mean) / std
        else:
            # RGB case
            normalized = (image - mean) / std
        
        return normalized

    def preprocess(self, image: np.ndarray) -> np.ndarray:
        """
        Full preprocessing pipeline: center crop -> resize -> normalize.
        
        Args:
            image: Input RGB image as numpy array (H, W, C) or (H, W)
                   Values can be uint8 [0-255] or float [0-1]
                   
        Returns:
            Preprocessed image as float32 numpy array of shape 
            (target_height, target_width, 3) normalized with mean/std
        """
        if not isinstance(image, np.ndarray):
            raise TypeError(f"Expected numpy array, got {type(image)}")
        
        if image.size == 0:
            raise ValueError("Input image is empty")
        
        # Step 1: Center crop
        cropped = self._center_crop(image)
        
        # Step 2: Resize to fixed resolution
        resized = self._resize(cropped)
        
        # Step 3: Normalize
        if self.config.normalize:
            normalized = self._normalize_image(resized)
        else:
            normalized = resized.astype(np.float32)
            if normalized.max() > 1.0:
                normalized = normalized / 255.0
        
        # Ensure final shape and dtype
        if normalized.ndim == 2:
            normalized = np.stack([normalized] * 3, axis=-1)
        
        return normalized


def create_rgb_preprocessor(config: Optional[RGBPreprocessingConfig] = None) -> RGBPreprocessor:
    """
    Factory function to create an RGB preprocessor.
    
    Args:
        config: Optional configuration object. If None, uses defaults or hyperparameters.
        
    Returns:
        Configured RGBPreprocessor instance
    """
    if config is None:
        # Try to load from hyperparameters
        try:
            target_h = get_hyperparameter("rgb_target_height", 84)
            target_w = get_hyperparameter("rgb_target_width", 84)
            config = RGBPreprocessingConfig(target_height=target_h, target_width=target_w)
        except Exception as e:
            logger.warning(f"Could not load RGB config from hyperparameters: {e}, using defaults")
            config = RGBPreprocessingConfig()
    
    return RGBPreprocessor(config)


def preprocess_rgb_batch(
    images: list[np.ndarray], 
    config: Optional[RGBPreprocessingConfig] = None
) -> list[np.ndarray]:
    """
    Preprocess a batch of RGB images.
    
    Args:
        images: List of input image arrays
        config: Optional configuration
                
    Returns:
        List of preprocessed image arrays
    """
    preprocessor = create_rgb_preprocessor(config)
    return [preprocessor.preprocess(img) for img in images]
