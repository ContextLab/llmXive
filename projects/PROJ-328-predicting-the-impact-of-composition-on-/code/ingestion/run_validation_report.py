"""
T019: Execute Validation Report Generation

This script runs the validation report generation pipeline.
It reads the ingestion status from data/processed/.ingestion_status.json
and generates the final validation report at data/processed/validation_report.yaml.

Dependencies:
- code/ingestion/generate_validation_report.py (T016b)
- data/processed/.ingestion_status.json (Output of T014)
"""

import os
import sys
import logging
import json
import yaml
from pathlib import Path

# Add the project root to the path so we can import code modules
# Assuming this script is run from the project root or code/ directory
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from ingestion.generate_validation_report import load_ingestion_status, generate_validation_report, save_report
from utils.logging_config import get_logger

def main():
    """
    Main entry point for T019.
    Executes the validation report generation.
    """
    logger = get_logger("T019_Validation_Report")
    logger.info("Starting T019: Execute Validation Report Generation")

    # Define paths relative to project root
    status_path = project_root / "data" / "processed" / ".ingestion_status.json"
    report_path = project_root / "data" / "processed" / "validation_report.yaml"

    # Verify input file exists
    if not status_path.exists():
        logger.error(f"Input file not found: {status_path}")
        logger.error("Prerequisite T014 has not been completed or the output path is incorrect.")
        sys.exit(1)

    try:
        # 1. Load the ingestion status
        logger.info(f"Loading ingestion status from: {status_path}")
        status_data = load_ingestion_status(status_path)
        
        if not status_data:
            logger.error("Failed to load ingestion status. File might be empty or malformed.")
            sys.exit(1)

        logger.debug(f"Loaded status: {status_data}")

        # 2. Generate the report content
        logger.info("Generating validation report content...")
        report_content = generate_validation_report(status_data)

        # 3. Save the report
        logger.info(f"Saving validation report to: {report_path}")
        save_report(report_content, report_path)

        logger.info("T019 completed successfully. Report generated.")
        print(f"SUCCESS: Validation report written to {report_path}")

    except FileNotFoundError as e:
        logger.error(f"File not found during processing: {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in status file: {e}")
        sys.exit(1)
    except yaml.YAMLError as e:
        logger.error(f"Error writing YAML report: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during T019 execution: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()