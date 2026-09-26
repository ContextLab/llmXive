"""
Image validation utilities.
"""
import cv2
import logging
import numpy as np
from pathlib import Path
from typing import List, Tuple, Optional, Set

from config import get_project_root, get_data_path
from utils.logging import get_logger, get_log_path

logger: logging.Logger = get_logger(__name__)

def validate_image(image_path: str | Path) -> bool:
    """
    Validate a single image file.

    Args:
        image_path: Path to the image.

    Returns:
        bool: True if valid, False otherwise.
    """
    path = Path(image_path)
    if not path.exists():
        return False
    
    try:
        img = cv2.imread(str(path))
        if img is None:
            return False
        if img.size == 0:
            return False
        return True
    except Exception:
        return False

def validate_batch(image_dir: str | Path, log_path: Optional[str | Path] = None) -> Tuple[List[str], List[str]]:
    """
    Validate all images in a directory.

    Args:
        image_dir: Directory containing images.
        log_path: Path to the validation log file.

    Returns:
        Tuple[List[str], List[str]]: (valid_files, invalid_files)
    """
    dir_path = Path(image_dir)
    if not dir_path.exists():
        raise FileNotFoundError(f"Directory not found: {dir_path}")

    valid_files: List[str] = []
    invalid_files: List[str] = []
    
    valid_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}

    for file_path in dir_path.iterdir():
        if file_path.suffix.lower() in valid_extensions:
            if validate_image(file_path):
                valid_files.append(file_path.name)
            else:
                invalid_files.append(file_path.name)
                logger.warning(f"Invalid image detected: {file_path.name}")

    # Write to log
    if log_path is None:
        log_path = get_log_path("validation.log")
    
    log_file = Path(log_path)
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(log_file, 'w') as f:
        f.write(f"Validation Log - {dir_path}\n")
        f.write(f"Valid: {len(valid_files)}\n")
        f.write(f"Invalid: {len(invalid_files)}\n")
        f.write("-" * 20 + "\n")
        for name in valid_files:
            f.write(f"VALID: {name}\n")
        for name in invalid_files:
            f.write(f"INVALID: {name}\n")

    return valid_files, invalid_files

def get_valid_images(image_dir: str | Path) -> List[Path]:
    """
    Get a list of valid image paths in a directory.

    Args:
        image_dir: Directory containing images.

    Returns:
        List[Path]: List of valid image paths.
    """
    dir_path = Path(image_dir)
    valid_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
    valid_paths: List[Path] = []

    for file_path in dir_path.iterdir():
        if file_path.suffix.lower() in valid_extensions:
            if validate_image(file_path):
                valid_paths.append(file_path)
    
    return valid_paths

def get_invalid_images(image_dir: str | Path) -> List[Path]:
    """
    Get a list of invalid image paths in a directory.

    Args:
        image_dir: Directory containing images.

    Returns:
        List[Path]: List of invalid image paths.
    """
    dir_path = Path(image_dir)
    valid_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
    invalid_paths: List[Path] = []

    for file_path in dir_path.iterdir():
        if file_path.suffix.lower() in valid_extensions:
            if not validate_image(file_path):
                invalid_paths.append(file_path)
    
    return invalid_paths
