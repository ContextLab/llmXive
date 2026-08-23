import os
import json
import logging
import argparse
from typing import Dict, Any, Optional

import pandas as pd

from code.data.paths import get_processed_path, get_results_path, get_raw_path, ensure_dir
from code.utils.logging import init_logging, get_exclusion_log_path

logger = logging.getLogger(__name__)

def load_exclusion_log() -> pd.DataFrame:
    """
    Load the exclusion log CSV.
    
    Returns:
        pd.DataFrame: The exclusion log with columns including 'Subject_ID'.
        
    Raises:
        FileNotFoundError: If the exclusion log does not exist.
    """
    log_path = get_exclusion_log_path()
    if not os.path.exists(log_path):
        raise FileNotFoundError(f"Exclusion log not found at {log_path}. Run motion filtering and behavioral validation first.")
    
    df = pd.read_csv(log_path)
    if 'Subject_ID' not in df.columns:
        raise ValueError("Exclusion log missing 'Subject_ID' column.")
    return df

def get_total_input_count() -> int:
    """
    Determine the total number of subjects that entered the pipeline.
    
    This counts the number of subject directories in the raw data folder
    (data/raw/HCP_1200/), which corresponds to the output of T012 (download).
    
    Returns:
        int: The count of subjects found in the raw data directory.
        
    Raises:
        FileNotFoundError: If the raw data directory does not exist or is empty.
    """
    raw_path = get_raw_path()
    if not os.path.exists(raw_path):
        raise FileNotFoundError(f"Raw data path not found: {raw_path}. Run download.py first.")
    
    # Count directories (subjects)
    subjects = [d for d in os.listdir(raw_path) if os.path.isdir(os.path.join(raw_path, d))]
    
    if not subjects:
        raise FileNotFoundError(f"No subject directories found in {raw_path}. Data download may have failed.")
    
    return len(subjects)

def calculate_success_rate() -> Dict[str, Any]:
    """
    Calculate the processing success rate (SC-001).
    
    Logic:
        1. Load total input count from raw data.
        2. Load exclusion log to count excluded subjects.
        3. Compute pro_processed = (Total_Input - Excluded) / Total_Input.
    
    Returns:
        Dict containing 'pro_processed' and metadata.
    """
    total_input = get_total_input_count()
    exclusion_df = load_exclusion_log()
    excluded_count = len(exclusion_df)
    
    if total_input == 0:
        raise ValueError("Total input count is 0; cannot calculate success rate.")
    
    pro_processed = (total_input - excluded_count) / total_input
    
    logger.info(f"Total Input Subjects: {total_input}")
    logger.info(f"Excluded Subjects: {excluded_count}")
    logger.info(f"Success Rate (pro_processed): {pro_processed:.4f}")
    
    return {
        "pro_processed": pro_processed,
        "total_input": total_input,
        "excluded_count": excluded_count,
        "remaining_count": total_input - excluded_count
    }

def save_success_rate(metrics: Dict[str, Any], output_path: Optional[str] = None) -> str:
    """
    Save the success rate metrics to a JSON file.
    
    Args:
        metrics: Dictionary containing the success rate data.
        output_path: Optional path to save the JSON. Defaults to data/results/success_rate.json.
        
    Returns:
        str: The path where the file was saved.
    """
    if output_path is None:
        results_dir = get_results_path()
        ensure_dir(results_dir)
        output_path = os.path.join(results_dir, "success_rate.json")
    
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Success rate metrics saved to {output_path}")
    return output_path

def run_success_rate_pipeline() -> Dict[str, Any]:
    """
    Run the full success rate calculation pipeline.
    
    Returns:
        Dict: The calculated metrics.
    """
    metrics = calculate_success_rate()
    save_success_rate(metrics)
    return metrics

def main():
    """Entry point for script execution."""
    init_logging()
    logger.info("Starting Success Rate Calculation (T015a)")
    
    try:
        metrics = run_success_rate_pipeline()
        logger.info(f"Pipeline completed successfully. Rate: {metrics['pro_processed']:.4f}")
    except (FileNotFoundError, ValueError) as e:
        logger.error(f"Pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()