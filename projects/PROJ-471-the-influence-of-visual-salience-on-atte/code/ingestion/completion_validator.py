import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

from config import get_paths, load_config
from utils.logging import get_logger

# Configure logger
logger = get_logger(__name__)

def count_source_images(source_dir: Path) -> int:
    """
    Count the number of source images in the raw dataset directory.
    Supports common image extensions: .png, .jpg, .jpeg, .bmp, .tiff.
    """
    if not source_dir.exists():
        logger.error(f"Source directory does not exist: {source_dir}")
        return 0

    extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif'}
    count = 0
    for item in source_dir.iterdir():
        if item.is_file() and item.suffix.lower() in extensions:
            count += 1
    
    logger.info(f"Found {count} source images in {source_dir}")
    return count

def count_generated_maps(output_dir: Path) -> int:
    """
    Count the number of generated salience maps in the output directory.
    Supports .npy and .png extensions as defined in T016.
    """
    if not output_dir.exists():
        logger.warning(f"Output directory does not exist: {output_dir}. Returning 0.")
        return 0

    extensions = {'.npy', '.png'}
    count = 0
    for item in output_dir.iterdir():
        if item.is_file() and item.suffix.lower() in extensions:
            count += 1
    
    logger.info(f"Found {count} generated salience maps in {output_dir}")
    return count

def validate_completeness(source_count: int, generated_count: int) -> Dict[str, Any]:
    """
    Compare source and generated counts to determine pass/fail status for SC-001.
    Returns a dictionary with validation details.
    """
    is_complete = (source_count > 0) and (source_count == generated_count)
    
    result = {
        "status": "PASS" if is_complete else "FAIL",
        "source_image_count": source_count,
        "generated_map_count": generated_count,
        "missing_count": max(0, source_count - generated_count),
        "excess_count": max(0, generated_count - source_count),
        "compliance_check": "SC-001",
        "message": "Salience map generation complete." if is_complete else "Salience map generation incomplete or mismatch detected."
    }

    if not is_complete:
        if source_count == 0:
            result["message"] = "No source images found to validate against."
        elif generated_count < source_count:
            result["message"] = f"Missing {result['missing_count']} salience maps."
        else:
            result["message"] = f"Excess {result['excess_count']} salience maps generated."
    
    return result

def write_report(validation_result: Dict[str, Any], output_path: Path) -> None:
    """
    Write the validation report to a JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(validation_result, f, indent=2)
    
    logger.info(f"Validation report written to {output_path}")

def main() -> int:
    """
    Main entry point for the completion validator.
    Aggregates counts, validates completeness, and writes the report.
    """
    try:
        config = load_config()
        paths = get_paths()

        # Define paths based on config
        source_dir = paths.raw_data / "stimuli" # Assuming raw stimuli are here
        output_dir = paths.processed_data / "salience_maps"
        report_path = paths.interim_data / "salience_validation_report.json"

        logger.info("Starting salience map completion validation...")
        logger.info(f"Source directory: {source_dir}")
        logger.info(f"Output directory: {output_dir}")

        # Count images
        source_count = count_source_images(source_dir)
        generated_count = count_generated_maps(output_dir)

        # Validate
        validation_result = validate_completeness(source_count, generated_count)

        # Write report
        write_report(validation_result, report_path)

        # Log final status
        if validation_result["status"] == "PASS":
            logger.info("VALIDATION PASSED: SC-001 Compliance Confirmed.")
            return 0
        else:
            logger.error(f"VALIDATION FAILED: {validation_result['message']}")
            return 1

    except Exception as e:
        logger.exception(f"Error during validation: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
