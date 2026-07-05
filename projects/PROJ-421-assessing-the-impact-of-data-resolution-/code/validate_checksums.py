"""
T016: Apply checksumming and metadata validation for all generated rasters.

This script iterates through all derived resolution rasters in `data/derived/`,
computes their SHA-256 checksums, validates basic metadata (file existence,
non-zero size), and writes the results to `data/results/checksum_manifest.json`.
"""

import os
import json
import hashlib
import logging
from pathlib import Path
from typing import Dict, Any, List

# Import project utilities
from utils import get_logger, checksum_file, get_raster_info, validate_raster_bounds

# Configure logging
logger = get_logger("validate_checksums")

# Project paths (relative to project root)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DERIVED_DIR = PROJECT_ROOT / "data" / "derived"
RESULTS_DIR = PROJECT_ROOT / "data" / "results"
MANIFEST_PATH = RESULTS_DIR / "checksum_manifest.json"

# Expected resolutions based on config (factors: 1, 2, 4, 8, 16)
# 30m, 60m, 120m, 240m, 480m
EXPECTED_FACTORS = [1, 2, 4, 8, 16]

def validate_raster_metadata(file_path: Path) -> Dict[str, Any]:
    """
    Validates metadata for a single raster file.
    Returns a dict with validation status and details.
    """
    result = {
        "path": str(file_path),
        "exists": file_path.exists(),
        "size_bytes": 0,
        "checksum": None,
        "metadata_valid": False,
        "error": None
    }

    if not result["exists"]:
        result["error"] = "File does not exist"
        return result

    try:
        stat = file_path.stat()
        result["size_bytes"] = stat.st_size
        if result["size_bytes"] == 0:
            result["error"] = "File is empty"
            return result

        # Compute checksum
        result["checksum"] = checksum_file(str(file_path))

        # Attempt to read raster info if it looks like a GeoTIFF
        if file_path.suffix.lower() == ".tif":
            try:
                # We rely on utils.get_raster_info which should handle rasterio internally
                # If rasterio is not available or file is corrupt, this will raise
                info = get_raster_info(str(file_path))
                result["metadata"] = info
                result["metadata_valid"] = True
                
                # Optional: Validate bounds if we have reference bounds
                # For now, just check that we could read the info
            except Exception as e:
                result["error"] = f"Failed to read raster metadata: {str(e)}"
                # Don't return early; we still have checksum
        else:
            result["metadata"] = {"note": "Not a .tif file"}
            result["metadata_valid"] = True

    except Exception as e:
        result["error"] = f"Validation failed: {str(e)}"

    return result

def run_validation() -> Dict[str, Any]:
    """
    Main validation loop. Scans derived directory, validates each raster,
    and returns a summary manifest.
    """
    if not DERIVED_DIR.exists():
        logger.error(f"Derived directory not found: {DERIVED_DIR}")
        return {"error": f"Directory not found: {DERIVED_DIR}", "files": []}

    files = list(DERIVED_DIR.glob("*.tif"))
    if not files:
        logger.warning(f"No .tif files found in {DERIVED_DIR}")
        return {"warning": "No .tif files found", "files": []}

    logger.info(f"Found {len(files)} raster files to validate")

    results = []
    success_count = 0
    fail_count = 0

    for file_path in sorted(files):
        logger.info(f"Validating: {file_path.name}")
        validation = validate_raster_metadata(file_path)
        results.append(validation)

        if validation["metadata_valid"] and validation["checksum"]:
            success_count += 1
        else:
            fail_count += 1
            logger.warning(f"Validation failed for {file_path.name}: {validation.get('error')}")

    manifest = {
        "total_files": len(files),
        "valid_count": success_count,
        "invalid_count": fail_count,
        "generated_at": "auto-generated-by-T016",
        "files": results
    }

    return manifest

def main():
    """Entry point for the validation script."""
    logger.info("Starting raster checksum and metadata validation (T016)")

    # Ensure results directory exists
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # Run validation
    manifest = run_validation()

    # Write manifest
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    logger.info(f"Validation complete. Manifest written to: {MANIFEST_PATH}")
    logger.info(f"Summary: {manifest.get('valid_count', 0)}/{manifest.get('total_files', 0)} files valid")

    # Return non-zero exit code if any files failed validation
    if manifest.get("invalid_count", 0) > 0:
        logger.error(f"{manifest['invalid_count']} files failed validation")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())