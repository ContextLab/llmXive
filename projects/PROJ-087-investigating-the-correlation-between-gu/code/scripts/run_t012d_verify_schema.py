"""
Script to run schema verification (Task T012d).

This script verifies the data source schema and writes the ingestion report.
"""
import sys
import os
import logging
import json
from pathlib import Path
from src.config import load_config
from src.ingestion import verify_schema, write_ingestion_report
from src.logging_config import setup_logger

# Setup logger
logger = setup_logger(__name__)

def main():
    """Main entry point for schema verification."""
    config = load_config()
    data_url = config.get('DATA_URL')
    
    if not data_url:
        logger.error("No DATA_URL found in configuration")
        write_ingestion_report(
            status="blocked",
            reason="No verified data source found in plan.md or config",
            measurement_status="unmeasurable"
        )
        sys.exit(1)
        
    logger.info(f"Verifying schema for: {data_url}")
    
    # Run schema verification
    success, message, info = verify_schema(data_url)
    
    if success:
        logger.info(f"Schema verification successful: {message}")
        write_ingestion_report(
            status="success",
            reason="Schema verification passed",
            measurement_status="measurable",
            extra_fields={'schema_info': str(info)} if info else {}
        )
        sys.exit(0)
    else:
        logger.error(f"Schema verification failed: {message}")
        write_ingestion_report(
            status="blocked",
            reason=f"Schema mismatch: {message}",
            measurement_status="unmeasurable",
            extra_fields={'schema_info': str(info)} if info else {}
        )
        sys.exit(1)

if __name__ == "__main__":
    main()