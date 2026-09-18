"""
Task T016b: Generate Validation Report Script.

Reads data/processed/.ingestion_status.json and generates
data/processed/validation_report.yaml.

Input Schema (from .ingestion_status.json):
- threshold_status (str): 'N>=100', '50<=N<100', 'N<50'
- exact_N (int): Total count of valid records
- excluded_count (int): Records excluded due to composition sum
- power_limitation_warning (str, optional): 'N < 50' if applicable

Output Schema (validation_report.yaml):
- status (str): Mapped from threshold_status
- count (int): exact_N
- excluded_count (int): excluded_count
- power_limitation_warning (str, optional): Present if applicable
"""
import os
import sys
import json
import yaml
import logging
import argparse
from pathlib import Path

# Ensure code/ is in path
code_root = Path(__file__).resolve().parent.parent
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from utils.logging_config import get_logger

def load_ingestion_status(status_path: Path) -> dict:
    """Load the ingestion status JSON file."""
    if not status_path.exists():
        raise FileNotFoundError(f"Ingestion status file not found: {status_path}")
    
    with open(status_path, 'r') as f:
        return json.load(f)

def generate_validation_report(status_data: dict) -> dict:
    """
    Transform ingestion status data into the validation report format.
    """
    report = {
        "status": status_data.get("threshold_status", "UNKNOWN"),
        "count": status_data.get("exact_N", 0),
        "excluded_count": status_data.get("excluded_count", 0),
    }
    
    if "power_limitation_warning" in status_data:
        report["power_limitation_warning"] = status_data["power_limitation_warning"]
    
    return report

def save_report(report_data: dict, output_path: Path):
    """Save the report as YAML."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        yaml.dump(report_data, f, default_flow_style=False, sort_keys=False)

def main():
    """
    Main entry point for generating the validation report.
    """
    logger = get_logger("generate_validation_report")
    logger.info("Starting validation report generation.")

    # Determine paths relative to project root
    # We assume the script is run from the project root or code/ directory
    # but we resolve paths relative to the code/ingestion location
    processed_dir = code_root / "data" / "processed"
    status_file = processed_dir / ".ingestion_status.json"
    output_file = processed_dir / "validation_report.yaml"

    try:
        # 1. Load Status
        logger.info(f"Loading ingestion status from: {status_file}")
        status_data = load_ingestion_status(status_file)
        logger.debug(f"Loaded status: {status_data}")

        # 2. Generate Report
        logger.info("Generating validation report.")
        report_data = generate_validation_report(status_data)

        # 3. Save Report
        logger.info(f"Saving report to: {output_file}")
        save_report(report_data, output_file)

        logger.info("Validation report generation completed successfully.")
        return 0

    except FileNotFoundError as e:
        logger.error(f"Required input file missing: {e}")
        return 1
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in status file: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during report generation: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate validation report from ingestion status.")
    args = parser.parse_args()
    sys.exit(main())