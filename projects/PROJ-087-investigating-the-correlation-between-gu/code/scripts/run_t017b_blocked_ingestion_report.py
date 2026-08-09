"""
T017b: Generate Blocked Ingestion Report

This script is triggered when the data feasibility check (T012a) or schema verification (T012d) fails.
It creates the required `data/processed/ingestion_report.json` with a blocked status.

Deliverable:
- data/processed/ingestion_report.json containing:
  {
    "status": "blocked",
    "reason": "No verified data source found",
    "measurement_status": "unmeasurable",
    "timestamp": "<ISO8601 timestamp>"
  }
"""
import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# Add the project root to the path to allow imports
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.config import load_config

def generate_blocked_ingestion_report(reason: str = "No verified data source found", output_path: str = None) -> dict:
    """
    Generates a blocked ingestion report JSON file.
    
    Args:
        reason: The specific reason for the block.
        output_path: Optional path to write the report. Defaults to config DATA_URL or standard path.
        
    Returns:
        The report dictionary.
    """
    config = load_config()
    
    if output_path is None:
        # Ensure the directory exists
        output_dir = Path(config.get('DATA_PROCESSED_DIR', 'data/processed'))
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / 'ingestion_report.json'
    else:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

    report = {
        "status": "blocked",
        "reason": reason,
        "measurement_status": "unmeasurable",
        "timestamp": datetime.utcnow().isoformat()
    }

    # Write the report to disk
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    logging.info(f"Blocked ingestion report generated at: {output_path}")
    logging.info(f"Reason: {reason}")
    
    return report

def main():
    """Main entry point for the script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Determine the reason based on context if needed, 
        # but for T017b specifically, the default "No verified data source found" is standard
        # unless T012d failed specifically due to schema mismatch (which might use T012d_gen logic).
        # T017b is generally for the T012a failure path.
        report = generate_blocked_ingestion_report()
        
        # Verify file exists
        config = load_config()
        output_dir = Path(config.get('DATA_PROCESSED_DIR', 'data/processed'))
        report_path = output_dir / 'ingestion_report.json'
        
        if report_path.exists():
            logging.info("Verification: ingestion_report.json exists.")
            with open(report_path, 'r') as f:
                content = json.load(f)
                required_keys = ["status", "reason", "measurement_status", "timestamp"]
                if all(key in content for key in required_keys):
                    logging.info("Verification: All required keys present.")
                    logging.info(f"Content: {content}")
                else:
                    logging.error("Verification: Missing required keys in report.")
                    sys.exit(1)
        else:
            logging.error("Verification: ingestion_report.json was not created.")
            sys.exit(1)
            
    except Exception as e:
        logging.error(f"Failed to generate blocked ingestion report: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()