"""
Task T019: Execute Validation Report Generation.
Runs the script from T016b to produce data/processed/validation_report.yaml.
Ensures prerequisites exist and verifies output.
"""
import os
import sys
import json
import yaml
from pathlib import Path
import logging

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.logging_config import get_logger
from ingestion.generate_validation_report import (
    load_ingestion_status,
    load_validation_metrics,
    generate_validation_report,
    save_report
)

logger = get_logger(__name__)

def ensure_status_file():
    """Ensure data/processed/.ingestion_status.json exists."""
    status_path = project_root / "data" / "processed" / ".ingestion_status.json"
    if not status_path.exists():
        logger.error(f"Missing required input: {status_path}")
        raise FileNotFoundError(f"Required file not found: {status_path}")
    return status_path

def ensure_metrics_file():
    """Ensure data/processed/validation_metrics.yaml exists."""
    metrics_path = project_root / "data" / "processed" / "validation_metrics.yaml"
    if not metrics_path.exists():
        logger.error(f"Missing required input: {metrics_path}")
        raise FileNotFoundError(f"Required file not found: {metrics_path}")
    return metrics_path

def run_generation_script():
    """Execute the generation logic from T016b."""
    logger.info("Loading ingestion status...")
    status_data = load_ingestion_status()
    
    logger.info("Loading validation metrics...")
    metrics_data = load_validation_metrics()
    
    logger.info("Generating validation report...")
    report_data = generate_validation_report(status_data, metrics_data)
    
    logger.info("Saving validation report...")
    save_report(report_data)
    
    return report_data

def verify_output():
    """Verify the output file was created and is valid."""
    output_path = project_root / "data" / "processed" / "validation_report.yaml"
    if not output_path.exists():
        logger.error(f"Output file not created: {output_path}")
        return False
    
    try:
        with open(output_path, 'r') as f:
            content = yaml.safe_load(f)
        if not isinstance(content, dict):
            logger.error(f"Output file is not a valid YAML dictionary: {output_path}")
            return False
        logger.info(f"Verification successful: {output_path}")
        return True
    except yaml.YAMLError as e:
        logger.error(f"Invalid YAML in output file: {e}")
        return False

def main():
    """Main entry point for T019."""
    logger.info("Starting T019: Execute Validation Report Generation")
    
    try:
        # 1. Ensure prerequisites
        ensure_status_file()
        ensure_metrics_file()
        
        # 2. Run generation
        run_generation_script()
        
        # 3. Verify output
        if not verify_output():
            logger.error("Verification failed. Exiting with error.")
            sys.exit(1)
        
        logger.info("T019 completed successfully.")
        sys.exit(0)
        
    except FileNotFoundError as e:
        logger.error(f"Prerequisite missing: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during T019 execution: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()