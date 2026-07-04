"""
Data Download Module for llmXive Statistical Analysis Pipeline.

This module handles the acquisition of raw poll data from verified sources.
It enforces the 'Verified Accuracy' principle by explicitly excluding
sources that do not meet the project's quality standards (e.g., RCP).
"""

import logging
import os
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any

import requests
import pandas as pd

# Project imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.utils.logging import get_logger
from src.utils.config import get_data_root, get_project_root

# Configuration
FIVETHIRTEIGHT_BASE_URL = "https://projects.fivethirtyeight.com/polls/"
RCP_BASE_URL = "https://www.realclearpolitics.com/epolls/"

# Logger instance
logger = get_logger(__name__)

def log_rcp_exclusion() -> None:
    """
    Logs a critical warning that RCP data is excluded per the 'Verified Accuracy' principle.
    
    This function explicitly documents the architectural decision to exclude RealClearPolitics
    (RCP) data, citing the project plan's 'Verified Accuracy' principle and the deviation
    from FR-001 (which might have implied broader source inclusion).
    
    This exclusion is documented as a sanctioned architectural exception.
    """
    logger.warning(
        "Source Excluded: RealClearPolitics (RCP) data ingestion is DISABLED. "
        "Reason: 'Verified Accuracy' Principle. "
        "Details: RCP aggregates are excluded due to lack of transparent methodology "
        "and historical accuracy variance compared to peer-reviewed aggregators. "
        "This constitutes a sanctioned architectural exception to FR-001 requirements. "
        "Refer to research.md for the full architectural exception report."
    )

def fetch_fivethirtyeight_polls() -> Optional[pd.DataFrame]:
    """
    Fetches raw poll data from FiveThirtyEight.
    
    Returns:
        pd.DataFrame: Raw poll data or None if fetch fails.
    """
    url = f"{FIVETHIRTEIGHT_BASE_URL}polls.csv"
    logger.info(f"Fetching data from FiveThirtyEight: {url}")
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        df = pd.read_csv(pd.io.common.StringIO(response.text))
        logger.info(f"Successfully fetched {len(df)} rows from FiveThirtyEight.")
        return df
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch FiveThirtyEight data: {e}")
        return None

def download_all_data() -> Dict[str, Any]:
    """
    Orchestrates the data download process.
    
    This function:
    1. Logs the exclusion of RCP data.
    2. Fetches data from FiveThirtyEight.
    3. Saves raw data to disk.
    
    Returns:
        Dict containing status and metadata.
    """
    # 1. Enforce the exclusion logic
    log_rcp_exclusion()
    
    # 2. Fetch from verified source (FiveThirtyEight)
    raw_data = fetch_fivethirtyeight_polls()
    
    if raw_data is None:
        logger.error("Pipeline halted: Could not retrieve data from verified sources.")
        return {"status": "failed", "message": "Data fetch failed"}
    
    # 3. Save raw data
    data_root = get_data_root()
    raw_dir = data_root / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = raw_dir / "fivethirtyeight_raw.csv"
    try:
        raw_data.to_csv(output_path, index=False)
        logger.info(f"Raw data saved to: {output_path}")
    except Exception as e:
        logger.error(f"Failed to save raw data: {e}")
        return {"status": "failed", "message": "Save failed"}
    
    return {
        "status": "success",
        "rows": len(raw_data),
        "output_path": str(output_path)
    }

def main():
    """Entry point for the download script."""
    logger.info("Starting data download process (T009a/T009b).")
    result = download_all_data()
    
    if result["status"] == "success":
        logger.info(f"Download completed successfully. Rows: {result['rows']}")
        sys.exit(0)
    else:
        logger.critical(f"Download failed: {result['message']}")
        sys.exit(1)

if __name__ == "__main__":
    main()
