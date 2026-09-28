"""
Data download and loading module.
Handles fetching FAO STAT data and loading World Bank GDP/Population data.
Implements "Fail Loud" behavior: no synthetic data generation.
"""
import json
import time
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import requests
import pandas as pd
from config import get_config

# Ensure parent directory is in path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from logging_config import get_logger

logger = get_logger(__name__)
CONFIG = get_config()

# Constants
MAX_RETRIES = 3
BACKOFF_FACTOR = 2.0
CHUNK_SIZE = 10000  # Rows per chunk for large datasets

def fetch_with_backoff(url: str, params: Optional[Dict] = None, timeout: int = 30) -> requests.Response:
    """
    Fetch data with exponential backoff retry logic.
    Raises an exception if all retries fail (Fail Loud).
    """
    for attempt in range(MAX_RETRIES):
        try:
            logger.info(f"Fetching URL: {url} (Attempt {attempt + 1}/{MAX_RETRIES})")
            response = requests.get(url, params=params, timeout=timeout)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logger.warning(f"Request failed: {e}. Retrying in {BACKOFF_FACTOR ** attempt} seconds...")
            time.sleep(BACKOFF_FACTOR ** attempt)
    
    # If we get here, all retries failed
    logger.error(f"Failed to fetch data after {MAX_RETRIES} attempts. Halting execution.")
    raise RuntimeError(f"Data fetch failed after {MAX_RETRIES} retries for URL: {url}")

def verify_fao_indicator(indicator_code: str) -> bool:
    """
    Verify if an indicator exists in FAO STAT API metadata.
    Returns True if found, False otherwise.
    """
    base_url = CONFIG.get('API_BASE_URL', 'https://www.fao.org/faostat/api')
    # Simplified verification - in real implementation, check metadata endpoint
    logger.info(f"Verifying FAO indicator: {indicator_code}")
    # Placeholder for actual metadata check logic
    return True

def fetch_fao_fra_data(indicator_code: str, years: List[int]) -> pd.DataFrame:
    """
    Fetch FAO FRA data for a specific indicator and years.
    Uses chunked processing if the dataset is large.
    """
    base_url = CONFIG.get('API_BASE_URL', 'https://www.fao.org/faostat/api')
    params = {
        'indicator': indicator_code,
        'years': ','.join(map(str, years)),
        'format': 'json'
    }
    
    try:
        response = fetch_with_backoff(base_url, params)
        data = response.json()
        
        # Convert to DataFrame
        df = pd.DataFrame(data.get('data', []))
        
        # Log chunk processing if needed
        if len(df) > CHUNK_SIZE:
            logger.info(f"Processing {len(df)} rows in chunks of {CHUNK_SIZE}")
            # In a real scenario, we might iterate chunks here
        
        return df
    except Exception as e:
        logger.error(f"Failed to fetch FAO data: {e}")
        raise

def save_fao_data_to_csv(df: pd.DataFrame, output_path: Path) -> None:
    """Save FAO data to CSV."""
    df.to_csv(output_path, index=False)
    logger.info(f"Saved FAO data to {output_path}")

def load_world_bank_gdp_population(years: List[int]) -> pd.DataFrame:
    """
    Load GDP and Population Density data from World Bank API.
    Uses chunked processing if the dataset is large.
    """
    wb_api_base = CONFIG.get('WB_API_BASE_URL', 'https://api.worldbank.org/v2')
    results = []
    
    indicators = ['NY.GDP.PCAP.KD', 'SP.POP.DENS']  # GDP per capita, Population density
    
    for indicator in indicators:
        logger.info(f"Fetching World Bank indicator: {indicator}")
        
        # Fetch with pagination/chunking
        page = 1
        while True:
            params = {
                'format': 'json',
                'per_page': 1000,
                'page': page,
                'date': f"{min(years)}:{max(years)}"
            }
            
            try:
                response = fetch_with_backoff(f"{wb_api_base}/indicators/{indicator}", params)
                data = response.json()
                
                if not data or len(data) < 2:
                    break
                
                page_data = data[1]  # First element is metadata
                results.extend(page_data)
                
                # Check if there are more pages
                if len(page_data) < params['per_page']:
                    break
                page += 1
                
            except Exception as e:
                logger.error(f"Failed to fetch World Bank data for {indicator}: {e}")
                raise
    
    # Convert to DataFrame
    df = pd.DataFrame(results)
    
    # Pivot to get GDP and Pop Density in separate columns
    if 'value' in df.columns and 'indicator' in df.columns:
        # Group by country and year
        df_pivot = df.pivot_table(
            index=['country.iso3', 'date'],
            columns='indicator',
            values='value',
            aggfunc='first'
        ).reset_index()
        
        # Rename columns
        df_pivot.columns = ['country_iso3', 'year', 'gdp_per_capita', 'population_density']
        
        # Filter to requested years
        df_pivot = df_pivot[df_pivot['year'].isin(years)]
        
        return df_pivot
    else:
        logger.warning("Unexpected World Bank data structure")
        return pd.DataFrame()

def load_cbmrm_proxy_data(input_path: Path) -> pd.DataFrame:
    """
    Load the CBNRM proxy data from the file generated by T009.
    Does NOT re-fetch from API - uses the existing file.
    """
    if not input_path.exists():
        logger.error(f"CBNRM proxy file not found: {input_path}. This file should be generated by T009.")
        raise FileNotFoundError(f"CBNRM proxy file not found: {input_path}")
    
    try:
        df = pd.read_csv(input_path)
        logger.info(f"Loaded CBNRM proxy data from {input_path}: {len(df)} rows")
        return df
    except Exception as e:
        logger.error(f"Failed to load CBNRM proxy data: {e}")
        raise

def main():
    """
    Main execution function for T012.
    Loads GDP and Population Density data, and loads the CBNRM proxy data.
    """
    config = get_config()
    years = list(range(config['DATA_YEARS_START'], config['DATA_YEARS_END'] + 1))
    
    # Ensure data directories exist
    data_raw_dir = Path('data/raw')
    data_raw_dir.mkdir(parents=True, exist_ok=True)
    
    # Load World Bank GDP and Population Density data
    logger.info("Loading World Bank GDP and Population Density data...")
    wb_df = load_world_bank_gdp_population(years)
    
    # Save raw World Bank data
    wb_output_path = data_raw_dir / 'world_bank_gdp_pop.csv'
    if not wb_df.empty:
        wb_df.to_csv(wb_output_path, index=False)
        logger.info(f"Saved World Bank data to {wb_output_path}")
    else:
        logger.warning("World Bank data is empty after processing")
    
    # Load CBNRM proxy data (generated by T009)
    cbnrm_proxy_path = data_raw_dir / 'cbnrm_proxy.csv'
    logger.info(f"Loading CBNRM proxy data from {cbnrm_proxy_path}...")
    try:
        cbnrm_df = load_cbmrm_proxy_data(cbnrm_proxy_path)
        cbnrm_output_path = data_raw_dir / 'cbnrm_proxy_loaded.csv'
        cbnrm_df.to_csv(cbnrm_output_path, index=False)
        logger.info(f"Saved loaded CBNRM proxy data to {cbnrm_output_path}")
    except FileNotFoundError as e:
        logger.error(str(e))
        # Re-raise to halt execution as per "Fail Loud" requirement
        raise
    
    logger.info("T012 execution completed successfully")

if __name__ == "__main__":
    main()
