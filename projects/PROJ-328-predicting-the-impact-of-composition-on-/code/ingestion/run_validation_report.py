"""
T019: Execute Validation Report Generation

This script runs the validation report generation logic defined in T016b.
It reads the ingestion status from data/processed/.ingestion_status.json
and produces data/processed/validation_report.yaml.

Dependencies:
- T016c (Verification of the script logic)
- T014 (Production of .ingestion_status.json)
"""

import os
import sys
import logging
import json
import yaml
from pathlib import Path

# Ensure the code directory is in the path for imports
code_root = Path(__file__).resolve().parent.parent
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from ingestion.generate_validation_report import load_ingestion_status, generate_validation_report, save_report
from utils.logging_config import get_logger
from utils.error_handlers import ConfigurationError

def main():
    """
    Main entry point for T019.
    Executes the validation report generation.
    """
    logger = get_logger("T019_validation_report")
    logger.info("Starting T019: Execute Validation Report Generation")

    # Define paths relative to project root
    project_root = code_root.parent
    status_file_path = project_root / "data" / "processed" / ".ingestion_status.json"
    report_output_path = project_root / "data" / "processed" / "validation_report.yaml"

    # Verify input file exists
    if not status_file_path.exists():
        error_msg = f"Input file not found: {status_file_path}. Did T014 run successfully?"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)

    try:
        # 1. Load ingestion status
        logger.info(f"Loading ingestion status from {status_file_path}")
        status_data = load_ingestion_status(status_file_path)

        # 2. Generate validation report
        logger.info("Generating validation report content")
        report_content = generate_validation_report(status_data)

        # 3. Save report
        logger.info(f"Saving validation report to {report_output_path}")
        save_report(report_content, report_output_path)

        logger.info(f"T019 completed successfully. Report saved to {report_output_path}")
        print(f"SUCCESS: Validation report generated at {report_output_path}")

    except ConfigurationError as ce:
        logger.error(f"Configuration error during report generation: {ce}")
        raise
    except json.JSONDecodeError as je:
        logger.error(f"Invalid JSON in status file: {je}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during T019 execution: {e}")
        raise

if __name__ == "__main__":
    main()