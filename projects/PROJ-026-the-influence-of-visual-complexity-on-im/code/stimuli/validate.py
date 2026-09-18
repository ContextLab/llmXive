import cv2
import logging
from pathlib import Path
from typing import List, Tuple, Optional, Set

from config import get_project_root, get_data_path
from utils.logging import get_logger

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
        img = cv2.imread(str(image_path))
        if img is None:
            return False

        # Check if image is empty or all zeros
        if img.size == 0:
            return False

        if np.all(img == 0):
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
        extensions: Set of valid extensions (default: .jpg, .jpeg, .png)

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
    """Main entry point for validation."""
    root = get_project_root()
    stimuli_dir = root / "data" / "raw" / "stimuli"

    if not stimuli_dir.exists():
        logger.error(f"Stimuli directory not found: {stimuli_dir}")
        return

    valid, invalid = validate_batch(stimuli_dir)

    logger.info(f"Valid images: {len(valid)}")
    logger.info(f"Invalid images: {len(invalid)}")

    for img in invalid:
        logger.warning(f"Skipped: {img.name}")


if __name__ == "__main__":
    main()
