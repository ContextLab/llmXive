"""
Module to generate the validation report for the data preprocessing pipeline.

This script consumes the exclusion log generated during preprocessing
and writes a formatted validation report adhering to the FR-010 schema.
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Define paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
EXCLUSION_LOG_PATH = PROJECT_ROOT / "data" / "processed" / "exclusion_log.json"
VALIDATION_REPORT_PATH = PROJECT_ROOT / "data" / "validation_report.json"

def generate_validation_report(exclusion_log_path: Path, output_path: Path) -> Dict[str, Any]:
    """
    Reads the exclusion log and writes the validation report.

    Args:
        exclusion_log_path: Path to the input exclusion_log.json
        output_path: Path where the validation_report.json will be written

    Returns:
        The validation report dictionary

    Raises:
        FileNotFoundError: If the exclusion log does not exist
        json.JSONDecodeError: If the exclusion log is invalid JSON
    """
    if not exclusion_log_path.exists():
        raise FileNotFoundError(f"Exclusion log not found at {exclusion_log_path}")

    logger.info(f"Reading exclusion log from {exclusion_log_path}")
    with open(exclusion_log_path, "r", encoding="utf-8") as f:
        exclusion_data = json.load(f)

    # Validate schema of input
    if "excluded_count" not in exclusion_data or "missing_columns" not in exclusion_data:
        raise ValueError("Exclusion log missing required keys: 'excluded_count' or 'missing_columns'")

    # Construct the report adhering to FR-010 schema
    report: Dict[str, Any] = {
        "excluded_count": int(exclusion_data["excluded_count"]),
        "missing_columns": list(exclusion_data["missing_columns"])
    }

    logger.info(f"Writing validation report to {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    logger.info(f"Validation report generated successfully: {report}")
    return report

def main() -> int:
    """
    Entry point for the validation report generator.
    """
    try:
        generate_validation_report(EXCLUSION_LOG_PATH, VALIDATION_REPORT_PATH)
        return 0
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in exclusion log: {e}")
        return 2
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        return 3
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 4

if __name__ == "__main__":
    exit(main())