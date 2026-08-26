"""
Aggregate Results Data (T060a)

This script aggregates results from statistical analyses (T024a, T024b, T025, T027)
and status counts (T064) into a single intermediate JSON file:
data/processed/report_data.json

It serves as the input for the final report generation (T060c).

Dependencies:
- T024a: data/processed/statistical_results.json (Clean)
- T024b: data/processed/statistical_results_noisy.json (Noisy)
- T025: data/processed/correlation_results.json
- T064: data/processed/status_counts.json
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define paths relative to project root
# The script is at code/report/aggregate_results.py, so root is 3 levels up
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

# Input file paths (matching the outputs of previous tasks)
# T024a: Statistical Analysis (Clean) - Output from T024a
STAT_CLEAN_PATH = DATA_PROCESSED_DIR / "statistical_results.json"
# T024b: Statistical Analysis (Noisy) - Output from T024b
# Note: T024b description says it outputs to statistical_results.json, but we assume
# the runner distinguishes clean vs noisy by filename or the task T024b overwrites
# or saves a separate file. Based on T024b description, it likely writes to the same
# file or a distinct one. Let's assume standard naming convention:
STAT_NOISY_PATH = DATA_PROCESSED_DIR / "statistical_results_noisy.json"

# T025: Point-Biserial Correlation - Output from T025
CORRELATION_PATH = DATA_PROCESSED_DIR / "correlation_results.json"

# T027: Threshold & Inflection Analysis - Output from T027
THRESHOLD_PATH = DATA_PROCESSED_DIR / "threshold_analysis.json"

# T064: Status Counts - Output from T064
STATUS_COUNTS_PATH = DATA_PROCESSED_DIR / "status_counts.json"

# Output file path
OUTPUT_PATH = DATA_PROCESSED_DIR / "report_data.json"


def load_json_file(file_path: Path) -> Optional[Dict[str, Any]]:
    """
    Load a JSON file and return its contents.
    Returns None if the file does not exist or cannot be parsed.
    Logs a warning but does not crash if a file is missing, allowing
    the aggregation to proceed with partial data where possible.
    """
    if not file_path.exists():
        logger.warning(f"Input file not found: {file_path}")
        return None

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from {file_path}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error reading {file_path}: {e}")
        return None


def aggregate_results() -> Dict[str, Any]:
    """
    Aggregate all result dictionaries into a single structure.
    """
    logger.info("Starting aggregation of results...")

    # Load all input files
    # Note: T024a and T024b might produce one file 'statistical_results.json' containing both,
    # or separate files. We handle the primary expected output from T024a/T024b logic.
    # Based on T024a description: "Output: data/processed/statistical_results.json"
    stat_clean = load_json_file(STAT_CLEAN_PATH)
    
    # If T024b produced a separate file, load it. If not, we might need to parse the main one.
    # For robustness, we try the specific noisy file first.
    stat_noisy = load_json_file(STAT_NOISY_PATH)
    
    correlation = load_json_file(CORRELATION_PATH)
    threshold = load_json_file(THRESHOLD_PATH)
    status_counts = load_json_file(STATUS_COUNTS_PATH)

    # Construct the aggregated report
    # We structure the data logically for the final report generator
    report = {
        "statistical_analysis": {
            "clean": stat_clean,
            "noisy": stat_noisy
        },
        "correlation_analysis": correlation,
        "threshold_analysis": threshold,
        "robustness_status_counts": status_counts,
        "metadata": {
            "generated_from": [
                {
                    "task": "T024a",
                    "path": str(STAT_CLEAN_PATH.relative_to(PROJECT_ROOT)) if STAT_CLEAN_PATH.exists() else None,
                    "exists": STAT_CLEAN_PATH.exists()
                },
                {
                    "task": "T024b",
                    "path": str(STAT_NOISY_PATH.relative_to(PROJECT_ROOT)) if STAT_NOISY_PATH.exists() else None,
                    "exists": STAT_NOISY_PATH.exists()
                },
                {
                    "task": "T025",
                    "path": str(CORRELATION_PATH.relative_to(PROJECT_ROOT)) if CORRELATION_PATH.exists() else None,
                    "exists": CORRELATION_PATH.exists()
                },
                {
                    "task": "T027",
                    "path": str(THRESHOLD_PATH.relative_to(PROJECT_ROOT)) if THRESHOLD_PATH.exists() else None,
                    "exists": THRESHOLD_PATH.exists()
                },
                {
                    "task": "T064",
                    "path": str(STATUS_COUNTS_PATH.relative_to(PROJECT_ROOT)) if STATUS_COUNTS_PATH.exists() else None,
                    "exists": STATUS_COUNTS_PATH.exists()
                }
            ],
            "output_file": str(OUTPUT_PATH.relative_to(PROJECT_ROOT))
        }
    }

    return report


def save_results(data: Dict[str, Any], output_path: Path) -> bool:
    """
    Save the aggregated data to a JSON file.
    """
    try:
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)

        logger.info(f"Successfully saved aggregated results to: {output_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to save results to {output_path}: {e}")
        return False


def main():
    """
    Main entry point for the aggregation script.
    """
    logger.info(f"Project root: {PROJECT_ROOT}")
    logger.info(f"Data directory: {DATA_PROCESSED_DIR}")

    # Aggregate results
    report_data = aggregate_results()

    # Save results
    success = save_results(report_data, OUTPUT_PATH)

    if success:
        logger.info("Aggregation completed successfully.")
        return 0
    else:
        logger.error("Aggregation failed due to I/O errors.")
        return 1


if __name__ == "__main__":
    exit(main())