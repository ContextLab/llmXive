"""
Service module for saving proxy extraction results.

Implements T026: Save extracted proxies to data/processed/proxy_results.csv
with columns: post_id, user_id, control_proxy, timestamp_regularity
"""

import logging
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional

from code.config import CONFIG
from code.services.proxy_extractor import run_proxy_extraction_pipeline

logger = logging.getLogger(__name__)

def save_proxy_results(
    proxy_data: List[Dict[str, Any]],
    output_path: Optional[Path] = None
) -> Path:
    """
    Save extracted proxy data to a CSV file.
    
    Args:
        proxy_data: List of dictionaries containing proxy extraction results
                   with keys: post_id, user_id, control_proxy, timestamp_regularity
        output_path: Optional custom output path. Defaults to CONFIG.PROXY_RESULTS_PATH
    
    Returns:
        Path to the saved CSV file
    
    Raises:
        ValueError: If proxy_data is empty or None
        IOError: If the file cannot be written
    """
    if output_path is None:
        output_path = CONFIG.PROXY_RESULTS_PATH
    
    if not proxy_data:
        raise ValueError("Cannot save empty proxy data. Ensure proxy extraction ran successfully.")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert to DataFrame and save
    df = pd.DataFrame(proxy_data)
    
    # Validate required columns exist
    required_columns = ['post_id', 'user_id', 'control_proxy', 'timestamp_regularity']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns in proxy data: {missing_columns}")
    
    # Ensure column order matches specification
    df = df[required_columns]
    
    # Save to CSV
    df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(df)} proxy records to {output_path}")
    
    return output_path

def run_proxy_saver_pipeline() -> Path:
    """
    Run the full proxy extraction and saving pipeline.
    
    This function orchestrates:
    1. Running proxy extraction on raw data (from T021)
    2. Saving results to data/processed/proxy_results.csv (T026)
    
    Returns:
        Path to the saved proxy_results.csv file
    """
    logger.info("Starting proxy extraction and saving pipeline")
    
    # Run proxy extraction
    proxy_data = run_proxy_extraction_pipeline()
    
    # Save results
    output_path = save_proxy_results(proxy_data)
    
    logger.info(f"Proxy extraction pipeline complete. Output: {output_path}")
    return output_path

def main():
    """Command-line entry point for proxy saver."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        output_path = run_proxy_saver_pipeline()
        print(f"Successfully saved proxy results to: {output_path}")
    except Exception as e:
        logger.error(f"Proxy saver pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()
