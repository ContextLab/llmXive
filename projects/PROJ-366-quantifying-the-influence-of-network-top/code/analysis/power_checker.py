"""
Statistical Power Check for Thermal Conductivity Analysis.

This module implements the statistical power check required before proceeding
with GNN training and correlation analysis. It validates the sample count N
after outlier filtering and determines if the dataset size is sufficient for
statistical power.

Requirements:
- N >= 10: Sufficient power (per Spec SC-004)
- 2 <= N < 10: Proceed with warning (per Plan proof-of-concept)
- N < 2: Exit with error code 1
"""

import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

from config import get_config, get_paths

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def count_valid_samples(conductivities_dir: Path) -> int:
    """
    Count the number of valid thermal conductivity samples in the processed directory.

    This function scans the `data/processed/conductivities/` directory and counts
    all valid thermal sample files (excluding excluded samples if the exclusion
    file exists).

    Args:
        conductivities_dir: Path to the directory containing processed conductivity samples.

    Returns:
        int: The count of valid samples (N).

    Raises:
        FileNotFoundError: If the conductivities directory does not exist.
        ValueError: If no valid samples are found.
    """
    if not conductivities_dir.exists():
        logger.error(f"Conductivities directory not found: {conductivities_dir}")
        raise FileNotFoundError(f"Conductivities directory not found: {conductivities_dir}")

    # Check for excluded samples file
    excluded_file = conductivities_dir.parent / "graphs" / "excluded_samples.json"
    excluded_ids: set = set()

    if excluded_file.exists():
        logger.info(f"Loading excluded samples from: {excluded_file}")
        try:
            with open(excluded_file, 'r') as f:
                excluded_data = json.load(f)
                excluded_ids = set(excluded_data.get('excluded_ids', []))
            logger.info(f"Found {len(excluded_ids)} excluded sample IDs")
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse excluded samples file: {e}. Proceeding without exclusion.")
    else:
        logger.info("No excluded samples file found. Proceeding with all samples.")

    # Count valid sample files
    valid_count = 0
    sample_files = list(conductivities_dir.glob("*.json"))

    for sample_file in sample_files:
        try:
            # Extract sample ID from filename (assuming format: sample_id.json)
            sample_id = sample_file.stem

            # Skip if excluded
            if sample_id in excluded_ids:
                logger.debug(f"Skipping excluded sample: {sample_id}")
                continue

            # Validate file content
            with open(sample_file, 'r') as f:
                sample_data = json.load(f)

            # Basic validation: must have conductivity value
            if 'conductivity' not in sample_data:
                logger.warning(f"Sample {sample_id} missing 'conductivity' field. Skipping.")
                continue

            valid_count += 1
            logger.debug(f"Valid sample found: {sample_id}")

        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to process sample file {sample_file}: {e}. Skipping.")
            continue

    if valid_count == 0:
        logger.error("No valid samples found after filtering.")
        raise ValueError("No valid samples found after filtering. Cannot proceed with analysis.")

    logger.info(f"Total valid samples (N): {valid_count}")
    return valid_count


def write_power_analysis_report(
    n_samples: int,
    output_path: Path,
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Write the statistical power analysis report to a JSON file.

    Args:
        n_samples: The number of valid samples (N).
        output_path: Path where the report will be written.
        config: Optional configuration dictionary for thresholds.

    Returns:
        Dict[str, Any]: The power analysis report dictionary.
    """
    # Determine status based on sample count
    if n_samples < 2:
        status = "INSUFFICIENT_SAMPLES"
        message = "Critical: Sample count is less than 2. Cannot perform statistical analysis."
        should_exit = True
    elif n_samples < 10:
        status = "INSUFFICIENT_POWER"
        message = "Warning: Sample count is less than 10 (N < 10). Statistical power is limited. Proceeding with proof-of-concept as per Plan."
        should_exit = False
    else:
        status = "SUFFICIENT_POWER"
        message = "Sample count meets minimum statistical power requirements (N >= 10)."
        should_exit = False

    # Build report
    report = {
        "sample_count": n_samples,
        "status": status,
        "message": message,
        "threshold_min": 2,
        "threshold_target": 10,
        "proceed": not should_exit
    }

    # Add configuration details if provided
    if config:
        report["config"] = {
            "min_samples": config.get("min_samples", 2),
            "target_samples": config.get("target_samples", 10)
        }

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write report to file
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Power analysis report written to: {output_path}")
    return report


def main() -> int:
    """
    Main entry point for the statistical power check.

    This function:
    1. Loads configuration
    2. Counts valid samples from the conductivities directory
    3. Writes the power analysis report
    4. Exits with appropriate code based on sample count

    Returns:
        int: Exit code (0 for success, 1 for critical failure)
    """
    try:
        # Load configuration
        config = get_config()
        paths = get_paths()

        logger.info("Starting statistical power check...")

        # Define paths
        conductivities_dir = paths["data_processed_conductivities"]
        output_file = paths["data_processed_model_outputs"] / "power_analysis.json"

        # Count valid samples
        n_samples = count_valid_samples(conductivities_dir)

        # Write report
        report = write_power_analysis_report(n_samples, output_file, config)

        # Determine exit code
        if report["status"] == "INSUFFICIENT_SAMPLES":
            logger.error("CRITICAL: Insufficient samples to proceed. Exiting.")
            return 1
        elif report["status"] == "INSUFFICIENT_POWER":
            logger.warning("WARNING: Insufficient statistical power, but proceeding as per Plan.")
            return 0
        else:
            logger.info("Statistical power check passed.")
            return 0

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error during power check: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
