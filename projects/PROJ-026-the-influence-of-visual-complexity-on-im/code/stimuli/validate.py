import cv2
import logging
import numpy as np
from pathlib import Path
from typing import List, Tuple, Optional, Set

from config import get_project_root, get_data_path
from utils.logging import get_logger, get_log_path

logger = get_logger(__name__)


def validate_image(image_path: Path) -> bool:
    """
    Validate a single image file for corruption.

    Args:
        image_path: Path to image file

    Returns:
        True if valid, False otherwise
    """
    if not image_path.exists():
        return False

    try:
        # cv2.imread returns None if the file cannot be read or is corrupted
        img = cv2.imread(str(image_path))
        if img is None:
            return False

        # Check if image is empty (size 0)
        if img.size == 0:
            return False

        # Check if image is completely black (all zeros) - often indicates corruption
        # We use a small threshold to account for compression artifacts if necessary,
        # but strictly 0 is a safe bet for "corrupted" in many contexts.
        # However, a valid black image is technically valid.
        # The task implies "corruption", so we check for read failure primarily.
        # If the image loads but is all zeros, it might be a valid black image.
        # We will rely on cv2 returning None for corruption.
        # Additional check: ensure dimensions are reasonable (e.g., at least 1x1)
        if img.shape[0] < 1 or img.shape[1] < 1:
            return False

        return True

    except Exception as e:
        logger.debug(f"Validation error for {image_path}: {e}")
        return False


def validate_batch(
    stimuli_dir: Path,
    extensions: Optional[Set[str]] = None
) -> Tuple[List[Path], List[Path]]:
    """
    Validate all images in a directory.

    Args:
        stimuli_dir: Directory containing images
        extensions: Set of valid extensions (default: .jpg, .jpeg, .png, .bmp, .tiff)

    Returns:
        Tuple of (valid_images, invalid_images)
    """
    if extensions is None:
        extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}

    if not stimuli_dir.exists():
        raise FileNotFoundError(f"Stimuli directory not found: {stimuli_dir}")

    valid_images = []
    invalid_images = []

    # Find all image files
    image_files = []
    for ext in extensions:
        image_files.extend(stimuli_dir.glob(f"*{ext}"))
        image_files.extend(stimuli_dir.glob(f"*{ext.upper()}"))

    logger.info(f"Found {len(image_files)} image files in {stimuli_dir}")

    for img_path in image_files:
        if validate_image(img_path):
            valid_images.append(img_path)
        else:
            invalid_images.append(img_path)
            logger.warning(f"Skipping corrupted/invalid image: {img_path}")

    logger.info(f"Validation complete: {len(valid_images)} valid, {len(invalid_images)} invalid")

    return valid_images, invalid_images


def get_valid_images(stimuli_dir: Path) -> List[Path]:
    """Get list of valid image paths."""
    valid, _ = validate_batch(stimuli_dir)
    return valid


def get_invalid_images(stimuli_dir: Path) -> List[Path]:
    """Get list of invalid image paths."""
    _, invalid = validate_batch(stimuli_dir)
    return invalid


def main() -> None:
    """Main entry point for validation.
    
    Iterates data/raw/stimuli/, attempts to open each image,
    and writes valid/invalid status to logs/validation.log.
    """
    root = get_project_root()
    stimuli_dir = root / "data" / "raw" / "stimuli"
    
    # Ensure logs directory exists
    log_path = get_log_path()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Setup logging specifically for this task if not already done
    # The global setup_logging usually handles this, but we ensure the file handler is active
    # for the validation log if the main logger is configured to write there.
    # Based on task description: "logs filenames to logs/validation.log"
    # We assume the global logger setup in T008 covers this, or we rely on the file path.
    
    if not stimuli_dir.exists():
        logger.error(f"Stimuli directory not found: {stimuli_dir}")
        # Create the directory to allow the script to run without crashing if empty
        stimuli_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created empty stimuli directory: {stimuli_dir}")
        return

    valid, invalid = validate_batch(stimuli_dir)

    # Log summary to the main log
    logger.info(f"Valid images: {len(valid)}")
    logger.info(f"Invalid images: {len(invalid)}")

    # Log detailed entries to the specific validation log file if needed,
    # but the task says "logs filenames to logs/validation.log".
    # The logger configured in T008 writes to logs/app.log.
    # To strictly satisfy "logs/validation.log", we can add a specific handler or
    # rely on the existing logger if it's configured to write to validation.log.
    # Given the constraint to extend existing API, and T008 sets up 'logs/app.log',
    # we will assume the 'logger' instance writes to the configured file.
    # However, to be precise about the file name 'validation.log', we will add a file handler
    # specifically for this log message if it doesn't exist, or just rely on the standard log.
    # Re-reading task: "logs filenames to logs/validation.log".
    # Let's ensure we write to that specific file.
    
    validation_log_path = root / "logs" / "validation.log"
    validation_log_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(validation_log_path, 'w') as f:
        f.write(f"Validation Report - {stimuli_dir}\n")
        f.write("-" * 40 + "\n")
        f.write(f"Total files scanned: {len(valid) + len(invalid)}\n")
        f.write(f"Valid: {len(valid)}\n")
        f.write(f"Invalid: {len(invalid)}\n")
        f.write("-" * 40 + "\n\n")
        
        f.write("VALID FILES:\n")
        for img in valid:
            f.write(f"  [OK] {img.name}\n")
        
        f.write("\nINVALID FILES:\n")
        for img in invalid:
            f.write(f"  [FAIL] {img.name}\n")
    
    logger.info(f"Validation log written to: {validation_log_path}")

    for img in invalid:
        logger.warning(f"Skipped: {img.name}")


if __name__ == "__main__":
    main()