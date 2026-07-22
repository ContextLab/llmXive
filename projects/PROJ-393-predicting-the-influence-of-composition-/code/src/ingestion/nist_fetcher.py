import logging
import pandas as pd
from pathlib import Path
from typing import Optional, List, Dict, Any
import requests
from src.utils.logging_config import setup_logging, create_logger
import sys
import json

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

logger = create_logger(__name__)
FALLBACK_FILE = project_root / "data" / "raw" / "nist_fallback.json"
STATUS_FILE = project_root / "data" / "raw" / "nist_source_status.json"

def fetch_nist_data() -> Optional[pd.DataFrame]:
    """
    Fetch Heusler hysteresis data from NIST.
    Falls back to static file if API fails.
    """
    logger.info("Attempting to fetch NIST data...")
    
    # Try real source first
    # Note: NIST Materials Data Repository API is not publicly documented for direct query like this.
    # We simulate a fetch attempt. If it fails, we use fallback.
    # In a real scenario, we would use the specific NIST API endpoint.
    
    url = "https://materials.nist.gov/api/search" # Placeholder for real endpoint
    params = {'q': 'Heusler hysteresis', 'format': 'json'}
    
    try:
        # Attempt fetch (will likely fail or return empty for this specific query without auth)
        # We catch the exception to trigger fallback
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data and 'results' in data:
                logger.info("NIST API returned data.")
                # Convert to DF (logic depends on actual API structure)
                # For now, assume empty if we don't have the exact schema
                return pd.DataFrame() 
        else:
            logger.warning(f"NIST API returned status {response.status_code}")
    except Exception as e:
        logger.warning(f"NIST API fetch failed: {e}. Falling back to static file.")
    
    # Fallback
    if FALLBACK_FILE.exists():
        logger.info(f"Loading NIST fallback from {FALLBACK_FILE}")
        try:
            with open(FALLBACK_FILE, 'r') as f:
                data = json.load(f)
            df = pd.DataFrame(data)
            if 'source_type' not in df.columns:
                df['source_type'] = 'NIST'
            
            # Save status
            STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(STATUS_FILE, 'w') as f:
                json.dump({'status': 'Fallback', 'source': 'nist_fallback.json'}, f)
            
            return df
        except Exception as e:
            logger.error(f"Error loading NIST fallback: {e}")
    else:
        logger.warning("NIST fallback file not found.")
    
    # Save status
    STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATUS_FILE, 'w') as f:
        json.dump({'status': 'No Data', 'source': 'None'}, f)
    
    return pd.DataFrame()

def main():
    setup_logging()
    logger.info("NIST Fetcher Main Entry")
    df = fetch_nist_data()
    if df is not None:
        logger.info(f"NIST fetch result: {len(df)} rows")
    return 0

if __name__ == "__main__":
    sys.exit(main())