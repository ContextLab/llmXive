import os
import sys
import logging
import csv
from pathlib import Path
from collections import defaultdict

# Setup logging
from src.utils.logging import setup_logger
logger = setup_logger("run_t018b_audit_trail")

from src.data.preprocessing import main as run_species_filter

def main():
    """
    Wrapper to execute T018b: Generate audit trail of excluded species.
    """
    logger.info("Starting T018b: Species Filter Audit Trail Generation")
    
    try:
        # Execute the species filtering logic which generates the audit file
        run_species_filter()
        
        # Verify output exists
        from src.utils.config import get_interim_data_dir
        audit_path = get_interim_data_dir() / "species_filtered.csv"
        
        if audit_path.exists():
            with open(audit_path, 'r') as f:
                count = sum(1 for _ in f) - 1  # Subtract header
            logger.info(f"Successfully generated audit trail: {audit_path} ({count} excluded records)")
        else:
            logger.error(f"Failed to generate audit trail: {audit_path} not found")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"T018b execution failed: {e}")
        raise

if __name__ == "__main__":
    main()