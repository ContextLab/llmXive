"""
Data Validation Script (T042)

Validates the integrity of the downloaded raw dataset.
1. Iterates through data/raw/
2. Checks image integrity (non-corrupt, correct format)
3. Checks for missing strength metadata (if manifest exists)
4. Counts invalid pairs
5. Outputs results/validation_report.json
6. Exits with code 1 if invalid_ratio > 1%, else 0.
"""
from __future__ import annotations

import csv
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Import project utilities
from utils.config import get_data_dir, get_results_dir, get_raw_dir
from utils.logging_config import get_logger

# Configure logger to be tolerant of different call signatures
logger = get_logger("validate")


def setup_logging() -> logging.Logger:
    """Setup logging for the validation script."""
    # The logger from logging_config is a ReproducibilityLogger which is tolerant.
    # We return it. It handles the 'log_file' argument gracefully if passed,
    # or ignores it if not, satisfying all callers.
    return get_logger("validate")


def load_manifest(manifest_path: Path) -> List[Dict[str, str]]:
    """Load the manifest CSV if it exists."""
    if not manifest_path.exists():
        return []
    records = []
    with open(manifest_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(row)
    return records


def validate_image_exists(image_path: Path) -> bool:
    """Check if the image file exists."""
    return image_path.exists()


def validate_image_integrity(image_path: Path) -> Tuple[bool, str]:
    """
    Verify image integrity by attempting to open it.
    Returns (is_valid, error_message).
    Since we don't strictly depend on PIL in this specific validation step
    (to avoid import errors if not installed yet, though requirements.txt has it),
    we check file size and extension first.
    If PIL is available, we try to open it.
    """
    if not image_path.exists():
        return False, "File does not exist"

    # Basic extension check
    ext = image_path.suffix.lower()
    if ext not in [".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif"]:
        return False, f"Unsupported extension: {ext}"

    # Check file size (should be > 0)
    if image_path.stat().st_size == 0:
        return False, "File is empty"

    # Try to open with PIL if available
    try:
        from PIL import Image
        with Image.open(image_path) as img:
            img.verify()  # Verify integrity
        return True, ""
    except ImportError:
        # If PIL is not installed, we rely on the basic checks above.
        # This is acceptable for a validation script that might run in a minimal env,
        # but ideally PIL is present.
        return True, "PIL not installed, skipped deep verify"
    except Exception as e:
        return False, f"Corrupt image: {str(e)}"


def validate_pair(image_path: Path, metadata: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate a single image-metadata pair.
    """
    # 1. Check image existence and integrity
    is_valid, msg = validate_image_integrity(image_path)
    if not is_valid:
        return False, msg

    # 2. Check for missing strength metadata
    # Assuming metadata dict contains a key like 'yield_strength' or 'label'
    # If the manifest is missing the key, it's invalid.
    strength_keys = ['yield_strength', 'label', 'strength']
    found_key = None
    for key in strength_keys:
        if key in metadata:
            found_key = key
            break

    if not found_key:
        # If no strength key found, check if it's optional.
        # Per task T042: "check for missing strength metadata".
        # We assume it's required for a valid pair.
        return False, "Missing strength metadata"

    # Try to parse the strength value
    try:
        val = metadata[found_key]
        if val is None or val == "":
            return False, "Strength value is empty"
        float(val)
    except ValueError:
        return False, f"Invalid strength value: {metadata[found_key]}"

    return True, ""


def run_validation(raw_dir: Path, manifest_path: Path) -> Dict[str, Any]:
    """
    Run validation over all images in raw_dir.
    Returns a report dict.
    """
    if not raw_dir.exists():
        raise FileNotFoundError(f"Raw directory not found: {raw_dir}")

    # Load manifest if available
    manifest_data = {}
    if manifest_path.exists():
        rows = load_manifest(manifest_path)
        for row in rows:
            # Assume 'filename' or 'image_id' is the key
            fname = row.get('filename') or row.get('image_id') or row.get('name')
            if fname:
                manifest_data[fname] = row

    total_count = 0
    invalid_count = 0
    invalid_details = []

    # Iterate through images in raw_dir
    # Support both flat and nested structures
    image_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif"}
    
    for root, _, files in os.walk(raw_dir):
        for file in files:
            if Path(file).suffix.lower() in image_extensions:
                total_count += 1
                image_path = Path(root) / file
                filename = file

                # Get metadata from manifest if available
                metadata = manifest_data.get(filename, {})

                is_valid, reason = validate_pair(image_path, metadata)
                if not is_valid:
                    invalid_count += 1
                    invalid_details.append({
                        "image": str(image_path.relative_to(raw_dir)),
                        "reason": reason
                    })

    invalid_ratio = invalid_count / total_count if total_count > 0 else 0.0

    return {
        "invalid_count": invalid_count,
        "total_count": total_count,
        "invalid_ratio": invalid_ratio,
        "invalid_details": invalid_details[:10]  # Limit details in report
    }


def write_validation_report(report: Dict[str, Any], output_path: Path) -> None:
    """Write the validation report to JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    logger.info(f"Validation report written to {output_path}")


def main() -> None:
    """Main entry point."""
    # Setup logging
    logger = setup_logging()
    logger.log("start_validation", operation="validate")

    try:
        raw_dir = get_raw_dir()
        # Manifest is usually in data/processed/ or data/raw/ depending on stage.
        # For T042 (after download), manifest might not exist yet or be in raw_dir.
        # We check common locations.
        manifest_path = get_data_dir() / "processed" / "manifest.csv"
        if not manifest_path.exists():
            manifest_path = get_data_dir() / "raw" / "manifest.csv"
        
        logger.info(f"Scanning directory: {raw_dir}")
        logger.info(f"Manifest path: {manifest_path}")

        report = run_validation(raw_dir, manifest_path)

        results_dir = get_results_dir()
        output_path = results_dir / "validation_report.json"
        write_validation_report(report, output_path)

        # Log summary
        logger.info(f"Total: {report['total_count']}, Invalid: {report['invalid_count']}, Ratio: {report['invalid_ratio']:.4f}")

        # Exit logic
        if report["invalid_ratio"] > 0.01:
            logger.error("Invalid ratio exceeds 1%. Exiting with code 1.")
            sys.exit(1)
        else:
            logger.info("Validation passed. Exiting with code 0.")
            sys.exit(0)

    except Exception as e:
        logger.error(f"Validation failed with error: {e}")
        # Write a failure report if possible
        try:
            results_dir = get_results_dir()
            output_path = results_dir / "validation_report.json"
            write_validation_report({
                "invalid_count": -1,
                "total_count": 0,
                "invalid_ratio": -1.0,
                "error": str(e)
            }, output_path)
        except:
            pass
        sys.exit(1)


if __name__ == "__main__":
    main()