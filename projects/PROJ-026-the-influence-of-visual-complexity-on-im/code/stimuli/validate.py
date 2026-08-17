import cv2
import logging
from pathlib import Path
from typing import List, Tuple, Optional, Set
from ..config import get_project_root, get_data_path
from ..utils.logging import get_logger

logger = get_logger(__name__)

def validate_image(image_path: str) -> bool:
    """
    Validate a single image file for corruption or unreadability.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        True if image is valid, False otherwise
    """
    try:
        img = cv2.imread(image_path)
        if img is None:
            logger.debug(f"Image failed to load: {image_path}")
            return False
        
        # Check if image is empty (all zeros)
        if np.all(img == 0):
            logger.debug(f"Image is empty: {image_path}")
            return False
        
        return True
    except Exception as e:
        logger.debug(f"Error validating image {image_path}: {e}")
        return False

def validate_batch(image_paths: List[str]) -> Tuple[List[str], List[str]]:
    """
    Validate a batch of image files.
    
    Args:
        image_paths: List of image file paths
        
    Returns:
        Tuple of (valid_images, invalid_images)
    """
    valid = []
    invalid = []
    
    for path in image_paths:
        if validate_image(path):
            valid.append(path)
        else:
            invalid.append(path)
            logger.warning(f"Skipping corrupted/invalid image: {path}")
    
    return valid, invalid

def get_valid_images(directory: Path) -> List[Path]:
    """
    Get all valid image files from a directory.
    
    Args:
        directory: Path to the directory containing images
        
    Returns:
        List of valid image paths
    """
    image_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif'}
    image_files = []
    
    for ext in image_extensions:
        image_files.extend(directory.glob(f'*{ext}'))
        image_files.extend(directory.glob(f'*{ext.upper()}'))
    
    valid_images = []
    for img_path in image_files:
        if validate_image(str(img_path)):
            valid_images.append(img_path)
        else:
            logger.warning(f"Skipping invalid image: {img_path.name}")
    
    return valid_images

def get_invalid_images(directory: Path) -> List[Path]:
    """
    Get all invalid image files from a directory.
    
    Args:
        directory: Path to the directory containing images
        
    Returns:
        List of invalid image paths
    """
    image_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif'}
    image_files = []
    
    for ext in image_extensions:
        image_files.extend(directory.glob(f'*{ext}'))
        image_files.extend(directory.glob(f'*{ext.upper()}'))
    
    invalid_images = []
    for img_path in image_files:
        if not validate_image(str(img_path)):
            invalid_images.append(img_path)
    
    return invalid_images

def main():
    """Main entry point for validation."""
    root = get_project_root()
    stimuli_dir = root / "data" / "raw" / "stimuli"
    
    if not stimuli_dir.exists():
        logger.error(f"Stimuli directory not found: {stimuli_dir}")
        return
    
    valid, invalid = validate_batch([str(p) for p in stimuli_dir.glob('*')])
    logger.info(f"Valid images: {len(valid)}")
    logger.info(f"Invalid images: {len(invalid)}")

if __name__ == "__main__":
    main()
