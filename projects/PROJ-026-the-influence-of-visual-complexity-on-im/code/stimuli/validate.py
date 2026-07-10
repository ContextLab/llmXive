"""
Image validation utilities.
"""
import cv2
import logging
from pathlib import Path
from typing import List, Tuple, Optional

from ..config import get_project_root, get_data_path
from ..utils.logging import get_logger

logger = get_logger(__name__)

def validate_image(image_path: str) -> bool:
    """
    Validate a single image file.
    
    Args:
        image_path: Path to the image file.
        
    Returns:
        True if the image is valid, False otherwise.
    """
    try:
        img = cv2.imread(image_path)
        if img is None:
            return False
        # Check if image is empty or too small
        if img.size == 0:
            return False
        if img.shape[0] < 10 or img.shape[1] < 10:
            return False
        return True
    except Exception as e:
        logger.warning(f"Invalid image {image_path}: {e}")
        return False

def validate_batch(input_dir: str) -> List[Tuple[str, bool]]:
    """
    Validate all images in a directory.
    
    Args:
        input_dir: Path to the directory containing images.
        
    Returns:
        List of tuples (file_path, is_valid).
    """
    results = []
    input_path = Path(input_dir)
    
    if not input_path.exists():
        raise FileNotFoundError(f"Directory not found: {input_dir}")
        
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
    
    for file_path in input_path.iterdir():
        if file_path.suffix.lower() in image_extensions:
            is_valid = validate_image(str(file_path))
            results.append((str(file_path), is_valid))
            
    return results

def get_valid_images(input_dir: str) -> List[str]:
    """
    Get list of valid image paths in a directory.
    
    Args:
        input_dir: Path to the directory.
        
    Returns:
        List of valid image file paths.
    """
    return [f for f, v in validate_batch(input_dir) if v]

def get_invalid_images(input_dir: str) -> List[str]:
    """
    Get list of invalid image paths in a directory.
    
    Args:
        input_dir: Path to the directory.
        
    Returns:
        List of invalid image file paths.
    """
    return [f for f, v in validate_batch(input_dir) if not v]
