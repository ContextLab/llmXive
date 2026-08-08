"""
Script to generate the Blocked Analysis Report for T025b.
This task is triggered when T012c (Data Feasibility Check) fails,
indicating no verified data source was found.

It creates a `correlation_results.csv` file in `data/processed/`
with the status 'blocked' and the reason for the blockage.
"""
import os
import sys
import logging
import json
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.config import load_config
from src.logging_config import setup_logger

# Setup logging
logger = setup_logger("t025b_blocked_report")

def generate_blocked_analysis_report():
    """
    Generates the blocked correlation results CSV when data ingestion fails.
    """
    config = load_config()
    output_dir = project_root / "data" / "processed"
    output_file = output_dir / "correlation_results.csv"
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load the ingestion report to get the specific reason if available
    ingestion_report_path = project_root / "data" / "processed" / "ingestion_report.json"
    reason = "No verified data source found"
    ingestion_status = "blocked"
    
    if ingestion_report_path.exists():
        try:
            with open(ingestion_report_path, 'r') as f:
                ingestion_data = json.load(f)
                reason = ingestion_data.get('reason', reason)
                ingestion_status = ingestion_data.get('status', 'blocked')
        except Exception as e:
            logger.warning(f"Could not read ingestion report: {e}. Using default reason.")
    
    logger.info(f"Generating blocked analysis report with reason: {reason}")
    
    # Define the blocked result structure
    # The CSV needs columns that match the expected schema for downstream tasks
    # even if empty. Based on T024 requirements: [r, p, q, is_moderate, is_meaningful, status]
    blocked_data = {
        "r": [],
        "p": [],
        "q": [],
        "diversity_index": [],
        "sleep_metric": [],
        "is_moderate": [],
        "is_meaningful": [],
        "status": ["blocked"],
        "reason": [reason],
        "measurement_status": ["unmeasurable"]
    }
    
    try:
        import pandas as pd
        df_blocked = pd.DataFrame(blocked_data)
        
        # Save to CSV
        df_blocked.to_csv(output_file, index=False)
        
        logger.info(f"Successfully wrote blocked report to {output_file}")
        logger.info(f"File contains {len(df_blocked)} row(s) representing the blocked state.")
        
        # Verify file existence and non-empty content (header only is acceptable for blocked state)
        if output_file.exists() and output_file.stat().st_size > 0:
            logger.info("Verification: Blocked report file exists and is non-empty.")
            return True
        else:
            logger.error("Verification failed: File missing or empty.")
            return False
            
    except Exception as e:
        logger.error(f"Failed to generate blocked report: {e}")
        return False

def main():
    """
    Entry point for the script.
    """
    logger.info("Starting T025b: Generate Blocked Analysis Report")
    
    success = generate_blocked_analysis_report()
    
    if success:
        logger.info("T025b completed successfully.")
        sys.exit(0)
    else:
        logger.error("T025b failed to generate the report.")
        sys.exit(1)

if __name__ == "__main__":
    main()
