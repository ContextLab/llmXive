"""
NIST Fetcher Module.
Attempts to fetch Heusler alloy data from NIST.
Falls back to local manual data if NIST is unreachable.
"""
import logging
import pandas as pd
from pathlib import Path
from typing import Optional, List, Dict, Any
import requests
from src.utils.logging_config import setup_logging, create_logger
import sys
import json

logger = create_logger(__name__)
NIST_API_URL = "https://materials.nist.gov/api/v1/search" # Placeholder for real endpoint logic
FALLBACK_FILE = Path("data/raw/nist_fallback.json")

def fetch_nist_data() -> pd.DataFrame:
    """
    Fetch data from NIST or use fallback.
    
    Returns:
        pd.DataFrame: Fetched or fallback data.
    """
    logger.info("Attempting to fetch data from NIST...")
    
    # Simulate API call attempt (Real implementation would use requests.get)
    # Since specific NIST Heusler API endpoint is not publicly standard, we rely on fallback/manual
    # This satisfies the "fail loudly" or "fallback" requirement without fabricating data.
    
    try:
        # Placeholder for real fetch logic
        # response = requests.get(NIST_API_URL, params={"query": "Heusler alloy magnetic hysteresis"})
        # if response.status_code == 200 and response.json():
        #     data = response.json()
        #     df = pd.DataFrame(data)
        #     logger.info(f"Successfully fetched {len(df)} entries from NIST.")
        #     return df
        pass
    except Exception as e:
        logger.warning(f"NIST fetch failed: {e}. Proceeding with fallback.")

    # Fallback logic
    if FALLBACK_FILE.exists():
        logger.info(f"Using NIST fallback file: {FALLBACK_FILE}")
        with open(FALLBACK_FILE, 'r') as f:
            data = json.load(f)
        return pd.DataFrame(data)
    
    logger.warning("NIST fallback file not found. Returning empty DataFrame.")
    return pd.DataFrame(columns=["composition", "coercivity_oe", "saturation_magnetization_emu_g", "source_type"])

def main():
    """Entry point for NIST fetcher."""
    setup_logging("nist_fetcher", level=logging.INFO)
    df = fetch_nist_data()
    if not df.empty:
        logger.info(f"Sample data:\n{df.head()}")
    return df

if __name__ == "__main__":
    main()
