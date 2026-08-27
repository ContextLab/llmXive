"""
Validation Report Generator

Consumes the exclusion log from preprocessing and generates a validation report.
"""

import os
import json
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def generate_validation_report(
    input_path: str,
    output_path: str
) -> dict:
    """
    Generates a validation report based on the exclusion log.

    Args:
        input_path (str): Path to the input exclusion_log.json
        output_path (str): Path where the validation_report.json will be saved

    Returns:
        dict: The generated validation report dictionary

    Raises:
        FileNotFoundError: If the input file does not exist
        json.JSONDecodeError: If the input file is not valid JSON
    """
    input_file = Path(input_path)
    output_file = Path(output_path)

    if not input_file.exists():
        logger.error(f"Input file not found: {input_path}")
        raise FileNotFoundError(f"Input file not found: {input_path}")

    logger.info(f"Reading exclusion log from {input_path}")
    with open(input_file, 'r', encoding='utf-8') as f:
        exclusion_data = json.load(f)

    # Validate expected schema
    if 'excluded_count' not in exclusion_data or 'missing_columns' not in exclusion_data:
        logger.error("Input JSON does not match expected schema: missing 'excluded_count' or 'missing_columns'")
        raise ValueError("Input JSON does not match expected schema")

    # Construct the validation report
    # The schema is identical to the exclusion log for this specific task requirement
    validation_report = {
        "excluded_count": exclusion_data["excluded_count"],
        "missing_columns": exclusion_data["missing_columns"]
    }

    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Writing validation report to {output_path}")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(validation_report, f, indent=2)

    logger.info("Validation report generation completed successfully")
    return validation_report


def main():
    """Main entry point for the script."""
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent.parent
    input_path = project_root / "data" / "processed" / "exclusion_log.json"
    output_path = project_root / "data" / "validation_report.json"

    try:
        generate_validation_report(str(input_path), str(output_path))
        logger.info(f"Report successfully generated at {output_path}")
    except FileNotFoundError as e:
        logger.error(f"File error: {e}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during report generation: {e}")
        raise


if __name__ == "__main__":
    main()