"""
T018b: Verify that at least 50 materials remain after filtering.

This script reads the computed metrics from data/processed/metrics.csv
and verifies that the final sample size is >= 50. It logs the count
and raises an error if the threshold is not met, ensuring the study
has sufficient statistical power before proceeding to modeling.
"""
import os
import sys
import csv
import logging
from pathlib import Path

# Add parent directory to path for imports if running as script
sys.path.insert(0, str(Path(__file__).parent))

from config import Config, initialize_environment

# Initialize config to ensure environment variables are loaded
initialize_environment()

def setup_verification_logger():
    """Configure logging for the verification step."""
    logger = logging.getLogger("sample_size_verification")
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger

def load_metrics_count(csv_path):
    """
    Load the metrics CSV and count the number of valid material entries.
    
    Args:
        csv_path (str): Path to the metrics CSV file.
        
    Returns:
        int: Number of rows (materials) in the CSV.
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Metrics file not found at {csv_path}")
    
    count = 0
    with open(csv_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Ensure the row has a material_id to count it as valid
            if row.get('material_id'):
                count += 1
    return count

def main():
    logger = setup_verification_logger()
    config = Config()
    
    # Define paths relative to project root
    project_root = Path(__file__).parent.parent
    metrics_path = project_root / "data" / "processed" / "metrics.csv"
    
    logger.info("Starting sample size verification (Task T018b)...")
    logger.info(f"Looking for metrics file at: {metrics_path}")
    
    try:
        count = load_metrics_count(str(metrics_path))
        logger.info(f"Final sample size after filtering: {count} materials.")
        
        min_required = 50
        if count >= min_required:
            logger.info(f"SUCCESS: Sample size ({count}) meets the minimum requirement of {min_required}.")
            return 0
        else:
            logger.error(f"FAILURE: Sample size ({count}) is below the minimum requirement of {min_required}.")
            logger.error("The study cannot proceed with sufficient statistical power.")
            return 1
            
    except FileNotFoundError as e:
        logger.error(f"Critical Error: {e}")
        logger.error("Cannot verify sample size because the metrics file is missing.")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during verification: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())