"""
Generate Validation Report Script (T016b).

Reads the ingestion status from data/processed/.ingestion_status.json
and generates a structured validation report at data/processed/validation_report.yaml.

This script ensures data consistency by explicitly reading threshold_status,
exact_N, and power_limitation_warning from the JSON state file produced by T014.
"""
import os
import sys
import logging
import json
import yaml
from pathlib import Path
from datetime import datetime

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.logging_config import get_logger
from utils.error_handlers import ConfigurationError

# Define paths relative to project root
PROCESSED_DIR = project_root / "data" / "processed"
STATUS_FILE = PROCESSED_DIR / ".ingestion_status.json"
REPORT_FILE = PROCESSED_DIR / "validation_report.yaml"

logger = get_logger(__name__)

def load_ingestion_status() -> dict:
    """
    Load the ingestion status from the JSON file.
    
    Raises:
        ConfigurationError: If the status file is missing or invalid.
    """
    if not STATUS_FILE.exists():
        raise ConfigurationError(
            f"Ingestion status file not found: {STATUS_FILE}. "
            "Ensure T014 (validator) has run successfully to generate this file."
        )
    
    try:
        with open(STATUS_FILE, 'r', encoding='utf-8') as f:
            status = json.load(f)
        logger.info(f"Successfully loaded ingestion status from {STATUS_FILE}")
        return status
    except json.JSONDecodeError as e:
        raise ConfigurationError(f"Invalid JSON in ingestion status file: {e}") from e

def generate_validation_report(status: dict) -> dict:
    """
    Construct the validation report dictionary from the ingestion status.
    
    Args:
        status: The dictionary loaded from .ingestion_status.json.
    
    Returns:
        A dictionary representing the validation report.
    """
    # Explicitly extract required fields as per T014 output schema
    # Schema: threshold_status (str), exact_N (int), power_limitation_warning (str)
    threshold_status = status.get('threshold_status', 'UNKNOWN')
    exact_n = status.get('exact_N', 0)
    power_limitation_warning = status.get('power_limitation_warning', '')
    
    # Map to output schema: status, count, power_limitation_warning
    report = {
        "report_metadata": {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "source_file": str(STATUS_FILE),
            "report_type": "Ingestion Validation Summary",
            "task_id": "T016b"
        },
        "status": threshold_status,
        "count": exact_n,
        "power_limitation_warning": power_limitation_warning,
        "associational_warning": "NOTE: Results are associational, not causal. See FR-007."
    }

    return report

def save_report(report: dict) -> None:
    """
    Save the generated report to the YAML file.
    
    Args:
        report: The report dictionary to save.
    """
    # Ensure directory exists
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    
    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        yaml.dump(report, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
    
    logger.info(f"Validation report successfully generated at {REPORT_FILE}")

def main():
    """Main entry point for the validation report generation."""
    try:
        logger.info("Starting validation report generation (T016b)...")
        
        # Step 1: Load status
        status = load_ingestion_status()
        
        # Step 2: Generate report
        report = generate_validation_report(status)
        
        # Step 3: Save report
        save_report(report)
        
        logger.info("Validation report generation completed successfully.")
        return 0
        
    except ConfigurationError as e:
        logger.error(f"Configuration error: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error during report generation: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())