"""
NIST Fetcher Module.
Attempts to fetch Heusler alloy data from NIST with robustness improvements:
- Timeout handling
- Retry logic with exponential backoff
- Streaming support for large responses
"""
import logging
import pandas as pd
from pathlib import Path
from typing import Optional, List, Dict, Any
import requests
from src.utils.logging_config import setup_logging, create_logger
import sys
import json
import time

logger = create_logger(__name__)
NIST_API_URL = "https://materials.nist.gov/api/v1/search"
FALLBACK_FILE = Path("data/raw/nist_fallback.json")

# Configuration for robustness
MAX_RETRIES = 3
INITIAL_RETRY_DELAY = 1.0  # seconds
TIMEOUT_SECONDS = 30

def fetch_nist_data() -> pd.DataFrame:
    """
    Fetch data from NIST with retry logic and timeout handling.
    
    Returns:
        pd.DataFrame: Fetched or fallback data.
    """
    logger.info("Attempting to fetch data from NIST with robustness checks...")
    
    last_exception = None
    
    for attempt in range(MAX_RETRIES):
        try:
            logger.info(f"NIST fetch attempt {attempt + 1}/{MAX_RETRIES}")
            
            # Use timeout to prevent hanging
            response = requests.get(
                NIST_API_URL, 
                params={"query": "Heusler alloy magnetic hysteresis"},
                timeout=TIMEOUT_SECONDS,
                stream=True  # Enable streaming for large responses
            )
            
            # Raise for HTTP errors
            response.raise_for_status()
            
            # Parse JSON from stream
            data = response.json()
            
            if not data:
                logger.warning("NIST API returned empty response.")
                break
                
            df = pd.DataFrame(data)
            logger.info(f"Successfully fetched {len(df)} entries from NIST.")
            return df
            
        except requests.exceptions.Timeout:
            last_exception = f"Timeout after {TIMEOUT_SECONDS}s"
            logger.warning(f"NIST fetch timeout: {last_exception}")
            
        except requests.exceptions.RequestException as e:
            last_exception = str(e)
            logger.warning(f"NIST fetch request failed: {e}")
            
        except json.JSONDecodeError as e:
            last_exception = f"Invalid JSON response: {e}"
            logger.warning(f"NIST fetch invalid JSON: {e}")
            break
            
        except Exception as e:
            last_exception = str(e)
            logger.warning(f"Unexpected error during NIST fetch: {e}")
            break
        
        # Exponential backoff before retry
        if attempt < MAX_RETRIES - 1:
            delay = INITIAL_RETRY_DELAY * (2 ** attempt)
            logger.info(f"Retrying in {delay:.1f} seconds...")
            time.sleep(delay)
    
    # If we exhausted retries or encountered a fatal error, proceed to fallback
    logger.warning(f"NIST fetch failed after {MAX_RETRIES} attempts: {last_exception}. Proceeding with fallback.")

    # Fallback logic
    if FALLBACK_FILE.exists():
        logger.info(f"Using NIST fallback file: {FALLBACK_FILE}")
        try:
            with open(FALLBACK_FILE, 'r') as f:
                data = json.load(f)
            df = pd.DataFrame(data)
            # Validate source_type
            if 'source_type' in df.columns:
                valid_entries = df[df['source_type'] == 'NIST']
                if len(valid_entries) > 0:
                    logger.info(f"Loaded {len(valid_entries)} valid NIST entries from fallback.")
                    return valid_entries
                else:
                    logger.warning("Fallback file exists but contains no entries with source_type='NIST'.")
        except Exception as e:
            logger.error(f"Failed to read NIST fallback file: {e}")
    
    logger.warning("NIST fallback file not found or invalid. Returning empty DataFrame.")
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
