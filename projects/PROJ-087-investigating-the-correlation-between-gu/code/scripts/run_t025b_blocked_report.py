"""
Script to generate the blocked correlation analysis report (T025b).
Triggered when T012a (Data Feasibility Check) or T012d (Schema Verification) fails.
Creates data/processed/correlation_results.csv with a blocked status.
"""
import os
import sys
import logging
import json
from pathlib import Path
from datetime import datetime
import pandas as pd

# Add project root to path for imports if running as script
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.config import load_config

def setup_logging():
    """Configure logging for the script."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(project_root / "logs" / "t025b_blocked_report.log")
        ]
    )
    return logging.getLogger(__name__)

def generate_blocked_analysis_report(logger: logging.Logger):
    """
    Generates the blocked correlation results CSV.
    
    This function creates data/processed/correlation_results.csv with:
    - status: "blocked"
    - reason: "No verified data source found"
    - Empty correlation columns (sample_id, diversity_index, sleep_metric, r, p, q, is_moderate, is_significant)
    """
    logger.info("Starting generation of blocked correlation analysis report (T025b).")
    
    # Load configuration
    config = load_config()
    output_dir = project_root / "data" / "processed"
    output_path = output_dir / "correlation_results.csv"
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Define columns for the blocked report
    columns = [
        "sample_id",
        "diversity_index",
        "sleep_metric",
        "r",
        "p",
        "q",
        "is_moderate",
        "is_significant",
        "status"
    ]
    
    # Create an empty DataFrame with the required columns
    # We add a single row to indicate the blocked status clearly
    blocked_data = {
        "sample_id": ["BLOCKED"],
        "diversity_index": ["N/A"],
        "sleep_metric": ["N/A"],
        "r": [None],
        "p": [None],
        "q": [None],
        "is_moderate": [None],
        "is_significant": [None],
        "status": ["blocked"]
    }
    
    df_blocked = pd.DataFrame(blocked_data)
    
    # Write to CSV
    try:
        df_blocked.to_csv(output_path, index=False)
        logger.info(f"Successfully wrote blocked report to {output_path}")
        
        # Log file existence and size for verification
        if output_path.exists():
            file_size = output_path.stat().st_size
            logger.info(f"Output file exists. Size: {file_size} bytes.")
        else:
            logger.error(f"Output file was not created at {output_path}")
            raise FileNotFoundError(f"Failed to create {output_path}")
            
    except Exception as e:
        logger.error(f"Failed to write blocked report: {e}")
        raise

def main():
    """Main entry point for T025b."""
    logger = setup_logging()
    try:
        generate_blocked_analysis_report(logger)
        logger.info("T025b completed successfully.")
        return 0
    except Exception as e:
        logger.error(f"T025b failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())