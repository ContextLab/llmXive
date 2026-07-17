import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple

from utils.config import get_results_dir, get_data_dir, get_processed_dir, get_seed, set_seed
from data.split import load_processed_manifest

def setup_logging() -> logging.Logger:
    """Configure and return the validation logger."""
    logger = logging.getLogger("validate")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        ))
        logger.addHandler(handler)
    return logger

def load_manifest(manifest_path: Path) -> List[Dict[str, Any]]:
    """Load the split manifest CSV/JSON."""
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")
    
    # Try JSON first, fallback to CSV if needed based on extension or content
    if manifest_path.suffix.lower() == '.json':
        with open(manifest_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        # Assuming CSV format as per split.py usage
        import csv
        data = []
        with open(manifest_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(row)
        return data

def validate_image_exists(image_path: Path) -> Tuple[bool, str]:
    """Check if the image file exists and is readable."""
    if not image_path.exists():
        return False, f"File not found: {image_path}"
    if image_path.stat().st_size == 0:
        return False, f"File is empty: {image_path}"
    return True, "OK"

def validate_pair(record: Dict[str, Any], data_dir: Path) -> Tuple[bool, str]:
    """
    Validate a single manifest record.
    Checks:
    1. Image file exists at the expected path.
    2. Yield strength value is present and numeric.
    """
    image_filename = record.get('image_filename') or record.get('image_id')
    if not image_filename:
        return False, "Missing image_filename or image_id"
    
    image_path = data_dir / image_filename
    exists, msg = validate_image_exists(image_path)
    if not exists:
        return False, msg

    strength = record.get('yield_strength')
    if strength is None:
        return False, "Missing yield_strength"
    
    try:
        val = float(strength)
        if not (0.0 < val < 10000.0): # Basic sanity check for MPa
            return False, f"Yield strength out of expected range: {val}"
    except (ValueError, TypeError):
        return False, f"Invalid yield_strength format: {strength}"

    return True, "Valid"

def run_validation(manifest_path: Path, data_dir: Path, logger: logging.Logger) -> Dict[str, Any]:
    """
    Run validation over the entire manifest.
    Returns a report dict.
    """
    logger.info(f"Loading manifest from {manifest_path}")
    records = load_manifest(manifest_path)
    logger.info(f"Loaded {len(records)} records")

    total = len(records)
    valid_count = 0
    invalid_records = []

    for i, record in enumerate(records):
        is_valid, reason = validate_pair(record, data_dir)
        if is_valid:
            valid_count += 1
        else:
            invalid_records.append({
                "index": i,
                "record": record,
                "reason": reason
            })
            logger.warning(f"Invalid record at index {i}: {reason}")

    invalid_count = total - valid_count
    invalid_ratio = invalid_count / total if total > 0 else 0.0

    report = {
        "manifest_path": str(manifest_path),
        "total_records": total,
        "valid_count": valid_count,
        "invalid_count": invalid_count,
        "invalid_ratio": invalid_ratio,
        "threshold": 0.01,
        "status": "PASS" if invalid_ratio <= 0.01 else "FAIL",
        "invalid_records_sample": invalid_records[:10] # Keep sample small
    }

    return report

def main():
    logger = setup_logging()
    
    # Determine paths
    data_dir = get_data_dir()
    # We expect the split manifests to be in data/processed/splits/ or similar
    # Based on split.py, it generates manifests in the data dir structure.
    # Usually 'test_manifest.csv' or similar. We look for the test manifest as validation is critical for the test set.
    processed_dir = get_processed_dir()
    split_dir = processed_dir / "splits"
    
    # Try to find the test manifest
    manifest_candidates = [
        split_dir / "test_manifest.csv",
        split_dir / "test_manifest.json",
        processed_dir / "test_manifest.csv",
        processed_dir / "test_manifest.json"
    ]
    
    manifest_path = None
    for candidate in manifest_candidates:
        if candidate.exists():
            manifest_path = candidate
            break
    
    if not manifest_path:
        logger.error("Could not find any test manifest in expected locations.")
        sys.exit(1)

    logger.info(f"Using manifest: {manifest_path}")

    report = run_validation(manifest_path, data_dir, logger)

    results_dir = get_results_dir()
    results_dir.mkdir(parents=True, exist_ok=True)
    output_path = results_dir / "validation_report.json"

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Validation report written to {output_path}")
    logger.info(f"Status: {report['status']} (Invalid Ratio: {report['invalid_ratio']:.4f})")

    if report['invalid_ratio'] > 0.01:
        logger.error("Invalid pair ratio exceeds 1% threshold. Exiting with code 1.")
        sys.exit(1)
    
    sys.exit(0)

if __name__ == "__main__":
    main()