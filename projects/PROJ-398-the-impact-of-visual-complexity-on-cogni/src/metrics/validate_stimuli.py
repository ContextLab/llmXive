import argparse
import logging
import os
import sys
from pathlib import Path
from typing import List, Optional, Tuple

import cv2
from PIL import Image

from src.config import PROJECT_ROOT, DATA_DIR

# Minimum resolution requirements
MIN_WIDTH = 640
MIN_HEIGHT = 360

def setup_logging(log_path: Path) -> logging.Logger:
    """Configure logging to write to the specified file and console."""
    logger = logging.getLogger("validate_stimuli")
    logger.setLevel(logging.INFO)

    # Clear existing handlers to avoid duplicates in repeated runs
    if logger.handlers:
        logger.handlers.clear()

    # File handler
    file_handler = logging.FileHandler(log_path)
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(file_formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

def validate_image_resolution(image_path: Path) -> Tuple[bool, Optional[str], Tuple[int, int]]:
    """
    Validate that an image is readable and meets minimum resolution.

    Returns:
        Tuple of (is_valid, error_message, (width, height))
    """
    try:
        # First, try to open with PIL to check readability
        with Image.open(image_path) as img:
            img.load()  # Ensure the file is actually readable
            width, height = img.size
    except Exception as e:
        return False, f"Failed to read image: {str(e)}", (0, 0)

    # Check resolution
    if width < MIN_WIDTH or height < MIN_HEIGHT:
        return False, f"Resolution {width}x{height} is below minimum {MIN_WIDTH}x{MIN_HEIGHT}", (width, height)

    return True, None, (width, height)

def validate_stimuli(
    stimuli_dir: Optional[Path] = None,
    log_path: Optional[Path] = None
) -> List[dict]:
    """
    Validate all images in the stimuli directory.

    Args:
        stimuli_dir: Directory containing stimulus images. Defaults to data/stimuli/raw/
        log_path: Path for the log file. Defaults to logs/validate_stimuli.log

    Returns:
        List of dictionaries containing validation results for each image.
    """
    # Resolve paths
    if stimuli_dir is None:
        stimuli_dir = DATA_DIR / "stimuli" / "raw"
    if log_path is None:
        log_path = PROJECT_ROOT / "logs" / "validate_stimuli.log"

    # Ensure log directory exists
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Setup logging
    logger = setup_logging(log_path)

    logger.info(f"Starting validation of stimuli in: {stimuli_dir}")
    logger.info(f"Minimum resolution: {MIN_WIDTH}x{MIN_HEIGHT}")

    # Check if directory exists
    if not stimuli_dir.exists():
        error_msg = f"Stimuli directory not found: {stimuli_dir}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)

    results = []
    valid_count = 0
    invalid_count = 0

    # Get all image files
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}
    image_files = [
        f for f in stimuli_dir.iterdir()
        if f.is_file() and f.suffix.lower() in image_extensions
    ]

    if not image_files:
        logger.warning(f"No image files found in {stimuli_dir}")
        return results

    logger.info(f"Found {len(image_files)} image files to validate")

    for img_path in sorted(image_files):
        is_valid, error_msg, dimensions = validate_image_resolution(img_path)
        result = {
            "image_id": img_path.stem,
            "image_path": str(img_path),
            "is_valid": is_valid,
            "dimensions": dimensions,
            "error": error_msg
        }
        results.append(result)

        if is_valid:
            logger.info(f"VALID: {img_path.name} ({dimensions[0]}x{dimensions[1]})")
            valid_count += 1
        else:
            logger.error(f"INVALID: {img_path.name} - {error_msg}")
            invalid_count += 1

    logger.info(f"Validation complete. Valid: {valid_count}, Invalid: {invalid_count}")

    return results

def main():
    """Main entry point for command-line execution."""
    parser = argparse.ArgumentParser(
        description="Validate stimuli images for readability and resolution."
    )
    parser.add_argument(
        "--stimuli-dir",
        type=Path,
        default=None,
        help=f"Path to stimuli directory (default: {DATA_DIR / 'stimuli' / 'raw'})"
    )
    parser.add_argument(
        "--log-path",
        type=Path,
        default=None,
        help=f"Path to log file (default: {PROJECT_ROOT / 'logs' / 'validate_stimuli.log'})"
    )

    args = parser.parse_args()

    try:
        results = validate_stimuli(
            stimuli_dir=args.stimuli_dir,
            log_path=args.log_path
        )

        # Print summary
        valid = sum(1 for r in results if r["is_valid"])
        invalid = len(results) - valid
        print(f"\nSummary: {valid} valid, {invalid} invalid out of {len(results)} images")

        if invalid > 0:
            sys.exit(1)  # Exit with error code if any images failed validation

    except Exception as e:
        print(f"Error during validation: {str(e)}", file=sys.stderr)
        sys.exit(2)

if __name__ == "__main__":
    main()
