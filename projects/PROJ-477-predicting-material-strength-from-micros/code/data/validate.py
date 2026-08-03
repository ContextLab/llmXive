"""
T042: Validate downloaded dataset integrity.

Checks:
1. Image files are not corrupt (can be opened by cv2).
2. Image files are in expected format (e.g., .png, .jpg).
3. Metadata (yield strength) exists for every image (via manifest or sidecar).

Output: results/validation_report.json
Exit: 1 if invalid_ratio > 0.01, else 0.
"""
import os
import sys
import json
import csv
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Any
import cv2
import numpy as np

# Import project utilities
from utils.config import get_results_dir, get_raw_dir, get_data_dir
from utils.logging_config import get_logger, log_operation


def setup_logging() -> logging.Logger:
    """Setup logging for the validation script."""
    logger = get_logger('validate', log_file='results/validation.log')
    # Return the logger object (which is a ReproducibilityLogger, but we treat it as a logger for logging purposes)
    # Since ReproducibilityLogger doesn't inherit from logging.Logger, we might need to adjust
    # But the task requires using get_logger. We will assume the ReproducibilityLogger is used directly.
    # However, for standard logging calls, we might need a bridge if the rest of the code expects stdlib.
    # Given the constraints, we will use the ReproducibilityLogger methods if available, 
    # but since the function signature says -> logging.Logger, we return the ReproducibilityLogger
    # which has been designed to be tolerant.
    return logger


def load_manifest(manifest_path: Path) -> List[Dict[str, Any]]:
    """Load the manifest CSV to map images to metadata."""
    if not manifest_path.exists():
        # If no manifest, we might rely on directory structure or fail if metadata is required
        # For this task, we assume a manifest.csv exists in data/raw/ or derived from directory structure
        return []
    
    records = []
    with open(manifest_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(row)
    return records


def validate_image_exists(image_path: Path) -> bool:
    """Check if the image file exists."""
    return image_path.exists()


def validate_image_integrity(image_path: Path) -> Tuple[bool, str]:
    """
    Attempt to read the image with OpenCV.
    Returns (is_valid, error_message).
    """
    if not image_path.exists():
        return False, "File does not exist"
    
    try:
        # Read image
        img = cv2.imread(str(image_path))
        if img is None:
            return False, "cv2.imread returned None (corrupt or unsupported format)"
        
        # Basic check: not all zeros (optional, but good for sanity)
        if np.all(img == 0):
            return False, "Image contains only zero values (potential corruption)"
        
        return True, "OK"
    except Exception as e:
        return False, str(e)


def validate_pair(image_path: Path, metadata: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate a single image and its metadata.
    Returns (is_valid, error_message).
    """
    # 1. Check image integrity
    is_valid, msg = validate_image_integrity(image_path)
    if not is_valid:
        return False, f"Image invalid: {msg}"
    
    # 2. Check metadata presence (e.g., yield strength)
    # The manifest should contain the strength value. 
    # If metadata is empty or missing key field, it's invalid.
    if not metadata:
        return False, "Missing metadata"
    
    # Assuming 'yield_strength' or similar key exists in manifest
    # We check for presence of at least one numeric value if expected
    # This depends on the manifest schema from T040/T013
    # Let's assume the manifest has 'yield_strength' or 'strength'
    strength_key = None
    for key in ['yield_strength', 'strength', 'value']:
        if key in metadata:
            strength_key = key
            break
    
    if strength_key is None:
        # If no known key found, check if ANY value exists that looks like strength
        # Or just assume valid if metadata exists and image is valid
        # For strict validation, we might fail if no strength key is found.
        # Let's be lenient: if image is valid and metadata exists, it's a pair.
        # But the task says "check for missing strength metadata".
        # We'll assume the manifest has a column 'yield_strength'
        return False, "Missing yield strength metadata in manifest"

    try:
        val = float(metadata[strength_key])
        if np.isnan(val) or np.isinf(val):
            return False, f"Invalid strength value: {val}"
    except (ValueError, TypeError):
        return False, f"Non-numeric strength value: {metadata[strength_key]}"

    return True, "OK"


def run_validation(raw_dir: Path, manifest_path: Path) -> Tuple[int, int, List[Dict]]:
    """
    Iterate through all images in raw_dir, validate against manifest.
    Returns (total_count, invalid_count, details_list).
    """
    total = 0
    invalid = 0
    details = []
    
    # Load manifest
    manifest_data = {}
    if manifest_path.exists():
        records = load_manifest(manifest_path)
        for rec in records:
            # Assume 'filename' or 'image_path' is the key
            fname = rec.get('filename') or rec.get('image_name') or rec.get('image_id')
            if fname:
                manifest_data[fname] = rec
    
    # Find images
    valid_extensions = {'.png', '.jpg', '.jpeg', '.tif', '.tiff', '.bmp'}
    image_files = []
    
    for ext in valid_extensions:
        image_files.extend(raw_dir.rglob(f"*{ext}"))
        image_files.extend(raw_dir.rglob(f"*{ext.upper()}"))
    
    for img_path in image_files:
        total += 1
        fname = img_path.name
        metadata = manifest_data.get(fname, {})
        
        is_valid, reason = validate_pair(img_path, metadata)
        
        if not is_valid:
            invalid += 1
            details.append({
                "image": str(img_path),
                "reason": reason,
                "status": "invalid"
            })
        else:
            details.append({
                "image": str(img_path),
                "reason": "OK",
                "status": "valid"
            })
    
    return total, invalid, details


def write_validation_report(report_path: Path, total: int, invalid: int) -> Dict:
    """Write the validation report JSON."""
    ratio = invalid / total if total > 0 else 0.0
    
    report = {
        "invalid_count": invalid,
        "total_count": total,
        "invalid_ratio": ratio
    }
    
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    return report


def main() -> None:
    """Main entry point for T042."""
    logger = setup_logging()
    log_operation("validation_start")
    
    try:
        raw_dir = get_raw_dir()
        results_dir = get_results_dir()
        
        # Manifest is typically in data/raw/ or data/processed/ after download
        # T040 outputs to data/raw/. T013 creates manifest in data/processed/.
        # For T042 (runs after T040, before T041), we look for manifest in data/raw/
        # If not there, we might scan the directory structure if manifest is missing.
        # However, T040 description says "Output: data/raw/ with original zip/images".
        # It implies the metadata might be in the zip or sidecar.
        # Let's assume a manifest.csv exists in raw_dir or we derive it.
        # If T040 created a manifest, it should be there.
        manifest_path = raw_dir / "manifest.csv"
        
        # If manifest doesn't exist in raw, maybe it's in processed? 
        # But T042 runs BEFORE T041 (preprocess) and T013 (split).
        # So manifest must be created by T040 or derived from filename patterns.
        # If T040 didn't create a manifest, we assume filenames encode strength or we fail.
        # Given the task: "check for missing strength metadata".
        # If no manifest, we cannot check metadata -> invalid.
        
        if not manifest_path.exists():
            logger.log("warning", "manifest.csv not found in data/raw/. Attempting to infer or fail.")
            # If we can't find metadata, we might have to skip metadata check or fail all.
            # Let's proceed with validation of images only if no manifest, 
            # but mark metadata missing as invalid if required.
            # For now, assume manifest exists or we treat missing manifest as 100% invalid metadata.
            pass

        total, invalid, details = run_validation(raw_dir, manifest_path)
        
        report_path = results_dir / "validation_report.json"
        report = write_validation_report(report_path, total, invalid)
        
        logger.log("validation_complete", total=total, invalid=invalid, ratio=report["invalid_ratio"])
        
        print(f"Validation Report: {report}")
        
        # Exit logic
        if report["invalid_ratio"] > 0.01:
            logger.log("error", "Invalid ratio exceeds 1% threshold.")
            sys.exit(1)
        else:
            logger.log("success", "Validation passed.")
            sys.exit(0)
            
    except Exception as e:
        logger.log("error", str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()