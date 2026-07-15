import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple

import cv2
import numpy as np

from src.lib.utils import set_global_seed

# Ensure reproducible behavior
set_global_seed(42)

def validate_stimuli(
    stimuli_dir: Path,
    min_width: int = 640,
    min_height: int = 360,
    log_file: Path | None = None
) -> Dict[str, Any]:
    """
    Validate that each image in stimuli_dir is readable and meets minimum resolution.
    
    Args:
        stimuli_dir: Path to directory containing stimulus images.
        min_width: Minimum required width in pixels.
        min_height: Minimum required height in pixels.
        log_file: Optional path to log file for validation results.
    
    Returns:
        Dictionary with keys:
            - 'total': total number of files checked
            - 'valid': number of valid images
            - 'invalid': list of dicts with 'path', 'reason', 'details'
    """
    # Setup logging
    logger = logging.getLogger("validate_stimuli")
    logger.setLevel(logging.INFO)
    
    # Remove existing handlers to avoid duplicates if called multiple times
    logger.handlers = []
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, mode='w')
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(file_handler)
    
    results = {
        'total': 0,
        'valid': 0,
        'invalid': []
    }
    
    # Supported image extensions
    valid_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}
    
    # Get all image files
    image_files = []
    for ext in valid_extensions:
        image_files.extend(stimuli_dir.glob(f'*{ext}'))
        image_files.extend(stimuli_dir.glob(f'*{ext.upper()}'))
    
    # Remove duplicates and sort for deterministic order
    image_files = sorted(set(image_files))
    
    logger.info(f"Found {len(image_files)} image files to validate.")
    
    for img_path in image_files:
        results['total'] += 1
        
        # Attempt to read image
        img = cv2.imread(str(img_path))
        
        if img is None:
            reason = "unreadable"
            details = "cv2.imread returned None (corrupted or unsupported format)"
            results['invalid'].append({
                'path': str(img_path),
                'reason': reason,
                'details': details
            })
            logger.warning(f"FAIL: {img_path.name} - {reason}: {details}")
            continue
        
        height, width = img.shape[:2]
        
        if width < min_width or height < min_height:
            reason = "undersized"
            details = f"Resolution {width}x{height} is below minimum {min_width}x{min_height}"
            results['invalid'].append({
                'path': str(img_path),
                'reason': reason,
                'details': details
            })
            logger.warning(f"FAIL: {img_path.name} - {reason}: {details}")
            continue
        
        # Image is valid
        results['valid'] += 1
        logger.info(f"PASS: {img_path.name} ({width}x{height})")
    
    logger.info(f"Validation complete: {results['valid']}/{results['total']} images passed.")
    return results


def main():
    """Main entry point for CLI execution."""
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent.parent.parent
    stimuli_dir = project_root / "data" / "stimuli"
    log_file = project_root / "logs" / "validate_stimuli.log"
    
    if not stimuli_dir.exists():
        print(f"Error: Stimuli directory not found at {stimuli_dir}")
        sys.exit(1)
    
    print(f"Validating stimuli in: {stimuli_dir}")
    results = validate_stimuli(stimuli_dir, log_file=log_file)
    
    print("\n--- Summary ---")
    print(f"Total files: {results['total']}")
    print(f"Valid: {results['valid']}")
    print(f"Invalid: {len(results['invalid'])}")
    
    if results['invalid']:
        print("\nFailed files:")
        for item in results['invalid']:
            print(f"  - {item['path']}: {item['reason']} ({item['details']})")
        sys.exit(0) # Exit 0 even if some failed, as the task is to log failures
    else:
        print("All stimuli validated successfully.")
        sys.exit(0)


if __name__ == "__main__":
    main()
