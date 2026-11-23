"""
Task T012e: Handle Schema Verification Failure

This script is executed when T012d (Schema Verification) fails.
It generates a blocked ingestion report to signal the pipeline that
the data source is invalid due to schema mismatch.

Output:
    data/processed/ingestion_report.json
        status: "blocked"
        reason: "Schema mismatch: Missing required columns"
        measurement_status: "unmeasurable"
"""
import os
import sys
import json
import logging
from pathlib import Path

# Add project root to path to allow imports from src
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.config import load_config
from src.utils.hashing import compute_sha256

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def generate_blocked_ingestion_report(reason: str = "Schema mismatch: Missing required columns") -> dict:
    """
    Generate the ingestion report indicating a blocked state due to schema failure.

    Args:
        reason: The specific reason for the block.

    Returns:
        dict: The report dictionary.
    """
    report = {
        "status": "blocked",
        "reason": reason,
        "measurement_status": "unmeasurable",
        "timestamp": None,  # Will be set by caller if needed, or left for downstream
        "details": {
            "missing_columns": [],  # Specifics would be populated by T012d, but T012e handles the failure state
            "verified_source": None
        }
    }
    return report

def main():
    """
    Main entry point for T012e.
    Generates the blocked report and writes it to disk.
    """
    config = load_config()
    output_dir = Path(config.get("DATA_PROCESSED_DIR", "data/processed"))
    output_path = output_dir / "ingestion_report.json"

    logger.info(f"Task T012e: Handling Schema Verification Failure.")
    logger.info(f"Target output path: {output_path}")

    # Ensure directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate the blocked report
    report = generate_blocked_ingestion_report(
        reason="Schema mismatch: Missing required columns"
    )

    # Write report to disk
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Successfully wrote blocked ingestion report to {output_path}")
        
        # Verify file exists and compute hash if needed for checksums
        if output_path.exists():
            file_hash = compute_sha256(str(output_path))
            logger.info(f"File hash: {file_hash}")
        else:
            logger.error("Failed to write file: path does not exist after write attempt.")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Failed to write ingestion report: {e}")
        sys.exit(1)

    logger.info("Task T012e completed successfully.")

if __name__ == "__main__":
    main()