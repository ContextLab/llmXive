"""
Module to save extracted control proxies to disk.
Implements T026: Save extracted proxies to data/processed/proxy_results.csv
"""
import logging
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional

from code.config import CONFIG
from code.services.proxy_extractor import run_proxy_extraction_pipeline

logger = logging.getLogger(__name__)

def save_proxy_results(proxy_data: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Saves the extracted proxy data to a CSV file.

    Args:
        proxy_data: List of dictionaries containing proxy metrics.
        output_path: Path where the CSV file will be saved.
    """
    if not proxy_data:
        logger.warning("No proxy data provided to save. Creating empty CSV with headers.")
        df = pd.DataFrame(columns=['post_id', 'user_id', 'control_proxy', 'timestamp_regularity'])
        df.to_csv(output_path, index=False)
        return

    df = pd.DataFrame(proxy_data)

    # Ensure expected columns exist and are in the correct order
    expected_cols = ['post_id', 'user_id', 'control_proxy', 'timestamp_regularity']
    
    # Check for missing columns (shouldn't happen if extractor is correct, but safety first)
    for col in expected_cols:
        if col not in df.columns:
            logger.error(f"Missing expected column in proxy data: {col}")
            raise ValueError(f"Missing expected column in proxy data: {col}")

    # Reorder columns to match specification exactly
    df = df[expected_cols]

    # Save to CSV
    df.to_csv(output_path, index=False)
    logger.info(f"Successfully saved {len(df)} proxy records to {output_path}")

def run_proxy_saver_pipeline() -> Path:
    """
    Orchestrates the extraction and saving of proxy results.
    1. Runs the extraction pipeline to get data.
    2. Saves the data to the configured output path.
    
    Returns:
        Path to the saved CSV file.
    """
    logger.info("Starting proxy saver pipeline...")
    
    # Extract data
    proxy_data = run_proxy_extraction_pipeline()
    
    # Define output path
    output_path = CONFIG.PROCESSED_DIR / "proxy_results.csv"
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save data
    save_proxy_results(proxy_data, output_path)
    
    logger.info("Proxy saver pipeline completed successfully.")
    return output_path

def main():
    """Entry point for running the proxy saver pipeline directly."""
    logging.basicConfig(level=logging.INFO)
    output_file = run_proxy_saver_pipeline()
    print(f"Proxy results saved to: {output_file}")

if __name__ == "__main__":
    main()
