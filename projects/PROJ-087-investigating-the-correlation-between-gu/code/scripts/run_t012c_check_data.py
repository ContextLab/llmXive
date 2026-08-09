import sys
import os
import logging
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import load_config
from src.ingestion import run_ingestion_pipeline, write_blocked_report, fetch_sample_headers, verify_schema

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Execute the data feasibility check (T012c)."""
    config = load_config()
    data_url = config.get('DATA_URL')

    if not data_url:
        logger.error("No DATA_URL found in configuration.")
        write_blocked_report("No verified data source found", "unmeasurable")
        return

    required_columns = ['antibiotic_use_last_3m', 'sleep_efficiency', 'sleep_duration_hours']
    logger.info(f"Fetching headers from {data_url}...")
    headers = fetch_sample_headers(data_url)

    if headers is None:
        logger.error("Failed to fetch headers from data source.")
        write_blocked_report("Failed to fetch headers", "unmeasurable")
        return

    logger.info(f"Fetched headers: {headers}")

    if not verify_schema(headers, required_columns):
        missing = [c for c in required_columns if c not in [h.strip().lower() for h in headers]]
        logger.error(f"Missing required columns: {missing}")
        write_blocked_report("Missing required columns", "unmeasurable")
        return

    logger.info("Data feasibility check PASSED. Schema verified.")
    # Write a success report (optional, but good for clarity)
    report_path = Path("data/processed/ingestion_report.json")
    with open(report_path, 'w') as f:
        json.dump({
            "status": "success",
            "message": "Data source verified and schema matches.",
            "measurement_status": "measurable"
        }, f, indent=2)
    logger.info(f"Success report written to {report_path}")

if __name__ == "__main__":
    main()