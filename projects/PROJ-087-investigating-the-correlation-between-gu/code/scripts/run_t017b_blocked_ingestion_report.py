"""
Script to generate the blocked ingestion report (T017b).
This script is triggered when the data feasibility check (T012a) or schema verification (T012d) fails.
It creates data/processed/ingestion_report.json with the required blocked status.
"""
import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# Add project root to path to allow imports if needed (though this script is standalone)
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def generate_blocked_ingestion_report(reason: str = "No verified data source found"):
    """
    Generates the ingestion report JSON indicating the project is blocked.

    Args:
        reason (str): The specific reason for the block.
    """
    output_dir = project_root / "data" / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "ingestion_report.json"

    report_data = {
        "status": "blocked",
        "reason": reason,
        "measurement_status": "unmeasurable",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2)
        
        logger.info(f"Successfully generated blocked ingestion report: {output_file}")
        logger.info(f"Report content: {json.dumps(report_data, indent=2)}")
        return True
    except IOError as e:
        logger.error(f"Failed to write ingestion report to {output_file}: {e}")
        raise

def main():
    """
    Main entry point for the script.
    """
    logger.info("Starting T017b: Generate Blocked Ingestion Report")
    
    # Default reason as per task description
    reason = "No verified data source found"
    
    # Allow overriding reason via command line argument if needed
    if len(sys.argv) > 1:
        reason = " ".join(sys.argv[1:])

    try:
        generate_blocked_ingestion_report(reason)
        logger.info("T017b completed successfully.")
        return 0
    except Exception as e:
        logger.error(f"T017b failed with error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())