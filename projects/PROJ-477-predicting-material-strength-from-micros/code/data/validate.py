"""
Validation script for downloaded material strength dataset.
Validates image integrity and label consistency.
"""
import os
import sys
import json
import csv
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config import get_data_dir, get_results_dir, get_project_root
from utils.logging_config import get_logger

# Constants
VALID_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}
MIN_IMAGE_SIZE = (32, 32)  # Minimum valid image dimensions

def setup_logging() -> logging.Logger:
    """Setup logging for validation script."""
    logger = get_logger('validate', log_file='results/validation.log')
    return logger

def load_manifest(manifest_path: Path) -> List[Dict[str, str]]:
    """Load the manifest CSV file."""
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest file not found: {manifest_path}")

    records = []
    with open(manifest_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(row)
    return records

def validate_image_exists(image_path: Path) -> Tuple[bool, Optional[str]]:
    """Check if image file exists and is readable."""
    if not image_path.exists():
        return False, f"File does not exist: {image_path}"

    if not image_path.is_file():
        return False, f"Not a file: {image_path}"

    # Check extension
    ext = image_path.suffix.lower()
    if ext not in VALID_IMAGE_EXTENSIONS:
        return False, f"Invalid extension: {ext}"

    # Try to read with OpenCV
    try:
        import cv2
        img = cv2.imread(str(image_path))
        if img is None:
            return False, "Failed to decode image (corrupted or unsupported format)"
        if img.size == 0:
            return False, "Image is empty"
        return True, None
    except Exception as e:
        return False, f"Error reading image: {str(e)}"

def validate_pair(record: Dict[str, str], base_dir: Path) -> Tuple[bool, Optional[str]]:
    """Validate a single image-label pair."""
    image_filename = record.get('image_filename', '')
    if not image_filename:
        return False, "Missing image_filename in manifest"

    image_path = base_dir / image_filename
    is_valid, error = validate_image_exists(image_path)
    if not is_valid:
        return False, error

    # Check for label existence if present
    label_value = record.get('yield_strength', '')
    if not label_value:
        return False, "Missing yield_strength label"

    try:
        float(label_value)
    except ValueError:
        return False, f"Invalid label value (not numeric): {label_value}"

    return True, None

def run_validation(manifest_path: Path, base_dir: Path, logger: logging.Logger) -> Dict:
    """Run validation on all records in manifest."""
    records = load_manifest(manifest_path)
    total_count = len(records)
    invalid_count = 0
    invalid_details = []

    logger.info(f"Validating {total_count} records from {manifest_path}")

    for i, record in enumerate(records):
        is_valid, error = validate_pair(record, base_dir)
        if not is_valid:
            invalid_count += 1
            invalid_details.append({
                'index': i,
                'image_filename': record.get('image_filename', 'UNKNOWN'),
                'error': error
            })
            logger.warning(f"Record {i} invalid: {error}")

        # Progress logging every 10%
        if (i + 1) % max(1, total_count // 10) == 0:
            logger.info(f"Progress: {i + 1}/{total_count} ({(i + 1) / total_count * 100:.1f}%)")

    invalid_ratio = invalid_count / total_count if total_count > 0 else 0.0

    result = {
        'invalid_count': invalid_count,
        'total_count': total_count,
        'invalid_ratio': round(invalid_ratio, 6),
        'invalid_details': invalid_details[:10]  # Log first 10 details
    }

    logger.info(f"Validation complete: {invalid_count}/{total_count} invalid ({invalid_ratio:.4f})")
    return result

def write_validation_report(result: Dict, output_path: Path) -> None:
    """Write validation report to JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
    logging.getLogger('validate').info(f"Report written to {output_path}")

def main():
    """Main entry point for validation script."""
    logger = setup_logging()
    logger.info("Starting dataset validation")

    try:
        project_root = get_project_root()
        data_dir = get_data_dir()
        results_dir = get_results_dir()

        # Determine manifest path (prefer processed manifest)
        manifest_path = data_dir / "processed" / "manifest.csv"
        if not manifest_path.exists():
            # Fallback to raw manifest if processed doesn't exist
            manifest_path = data_dir / "raw" / "manifest.csv"

        if not manifest_path.exists():
            logger.error(f"No manifest found at {manifest_path}")
            sys.exit(1)

        # Base directory depends on where manifest points
        # If manifest is in processed, base is processed; else raw
        if "processed" in str(manifest_path):
            base_dir = data_dir / "processed"
        else:
            base_dir = data_dir / "raw"

        # Run validation
        result = run_validation(manifest_path, base_dir, logger)

        # Write report
        output_path = results_dir / "validation_report.json"
        write_validation_report(result, output_path)

        # Exit with code 1 if invalid ratio > 1%
        if result['invalid_ratio'] > 0.01:
            logger.error(f"Invalid ratio {result['invalid_ratio']:.4f} exceeds threshold 0.01")
            sys.exit(1)

        logger.info("Validation passed")
        sys.exit(0)

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()