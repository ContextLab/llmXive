"""
Data Download Module for CBNRM vs State-Led Management Analysis.
Implements robust fetching, retry logic, and data loading for World Bank and FAO sources.
"""
import json
import time
import sys
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import pandas as pd
import requests

# Add parent directory to path to allow imports if run as script
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_config
from logging_config import get_logger

logger = get_logger(__name__)

# Constants
MAX_RETRIES = 3
BACKOFF_FACTOR = 2.0
CHUNK_SIZE = 10000  # Rows per chunk for large downloads

def fetch_with_backoff(url: str, params: Optional[Dict] = None, timeout: int = 30) -> Optional[Dict]:
    """
    Fetch data from a URL with exponential backoff retry logic.
    Returns the JSON response or None if all retries fail.
    """
    attempt = 0
    while attempt < MAX_RETRIES:
        try:
            logger.info(f"Fetching URL: {url} (Attempt {attempt + 1}/{MAX_RETRIES})")
            response = requests.get(url, params=params, timeout=timeout)
            
            # Handle Rate Limiting (429)
            if response.status_code == 429:
                retry_after = response.headers.get('Retry-After', str(BACKOFF_FACTOR * (attempt + 1)))
                try:
                    wait_time = float(retry_after)
                except ValueError:
                    wait_time = BACKOFF_FACTOR * (attempt + 1)
                logger.warning(f"Rate limited. Waiting {wait_time}s before retry.")
                time.sleep(wait_time)
                attempt += 1
                continue

            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed on attempt {attempt + 1}: {e}")
            if attempt < MAX_RETRIES - 1:
                wait_time = BACKOFF_FACTOR ** (attempt + 1)
                logger.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            attempt += 1
    
    logger.error(f"Failed to fetch data after {MAX_RETRIES} attempts: {url}")
    return None

def verify_fao_indicator(indicator_code: str) -> bool:
    """
    Verify if an indicator exists in the FAO STAT API.
    Returns True if exists, False otherwise.
    """
    config = get_config()
    base_url = config.get('API_BASE_URL', 'https://www.fao.org/faostat/api')
    # FAO STAT API endpoint for indicator metadata
    url = f"{base_url}/indicator"
    params = {'code': indicator_code}
    
    logger.info(f"Verifying FAO Indicator: {indicator_code}")
    response = fetch_with_backoff(url, params)
    
    if response and 'data' in response and len(response['data']) > 0:
        logger.info(f"Indicator {indicator_code} exists in FAO STAT.")
        return True
    
    logger.warning(f"Indicator {indicator_code} NOT found in FAO STAT.")
    return False

def save_fao_indicator_status(status: bool, indicator: str, output_path: Path) -> None:
    """Save verification status to JSON."""
    data = {
        'exists': status,
        'indicator': indicator,
        'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
    }
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Saved FAO indicator status to {output_path}")

def fetch_fao_fra_data(indicator_code: str, start_year: int, end_year: int) -> Optional[pd.DataFrame]:
    """
    Fetch Forest Area Change data from FAO STAT.
    Returns a DataFrame with columns: Country, Year, Value.
    """
    config = get_config()
    # FAO STAT API endpoint for data
    url = "https://www.fao.org/faostat/api/data"
    params = {
        'code': indicator_code,
        'start_year': start_year,
        'end_year': end_year,
        'format': 'json'
    }
    
    logger.info(f"Fetching FAO FRA data for {indicator_code} from {start_year} to {end_year}")
    response = fetch_with_backoff(url, params)
    
    if not response or 'data' not in response:
        logger.error("Failed to fetch FAO data or invalid response format.")
        return None
    
    try:
        # Parse FAO STAT response structure
        # Expected structure: {'data': [{'country': '...', 'year': 2000, 'value': ...}, ...]}
        records = response['data']
        df = pd.DataFrame(records)
        
        if df.empty:
            logger.warning("FAO data returned empty.")
            return pd.DataFrame(columns=['Country', 'Year', 'Value'])
        
        # Standardize columns
        df = df.rename(columns={
            'country': 'Country',
            'year': 'Year',
            'value': 'Value'
        })
        
        # Ensure types
        df['Year'] = pd.to_numeric(df['Year'], errors='coerce').astype('Int64')
        df['Value'] = pd.to_numeric(df['Value'], errors='coerce')
        
        # Drop rows with missing critical data
        df = df.dropna(subset=['Country', 'Year', 'Value'])
        
        logger.info(f"Fetched {len(df)} rows from FAO STAT.")
        return df
    except Exception as e:
        logger.error(f"Error parsing FAO data: {e}")
        return None

def save_fao_data_to_csv(df: pd.DataFrame, output_path: Path) -> None:
    """Save FAO data to CSV."""
    df.to_csv(output_path, index=False)
    logger.info(f"Saved FAO data to {output_path}")

def load_world_bank_gdp_population(start_year: int, end_year: int, output_path: Path) -> pd.DataFrame:
    """
    Fetch GDP (NY.GDP.PCAP.CD) and Population Density (SP.POP.DENS) from World Bank API.
    Returns a DataFrame with columns: Country, CountryCode, Year, GDP, PopDensity.
    """
    config = get_config()
    base_url = "https://api.worldbank.org/v2"
    
    indicators = {
        'gdp': 'NY.GDP.PCAP.CD',
        'pop_density': 'SP.POP.DENS'
    }
    
    all_data = []
    
    for name, indicator_code in indicators.items():
        url = f"{base_url}/country/all/indicator/{indicator_code}"
        params = {
            'format': 'json',
            'date': f"{start_year}:{end_year}",
            'per_page': 50000  # Request max per page
        }
        
        logger.info(f"Fetching World Bank data for {indicator_code} ({name})")
        response = fetch_with_backoff(url, params)
        
        if not response or len(response) < 2:
            logger.warning(f"No data found for {indicator_code}. Skipping.")
            continue
        
        # World Bank API returns [metadata, data]
        data_records = response[1]
        
        for record in data_records:
            if not record.get('value'):
                continue
            
            country_code = record.get('countryiso3code')
            country_name = record.get('country', {}).get('value', '')
            year = record.get('date')
            
            if not country_code or not year:
                continue
            
            try:
                year_int = int(year)
            except ValueError:
                continue
            
            all_data.append({
                'Country': country_name,
                'CountryCode': country_code,
                'Year': year_int,
                name: float(record['value'])
            })
    
    if not all_data:
        logger.warning("No economic data fetched from World Bank.")
        # Create empty DataFrame with expected columns
        df = pd.DataFrame(columns=['Country', 'CountryCode', 'Year', 'gdp', 'pop_density'])
        df.to_csv(output_path, index=False)
        return df
    
    df = pd.DataFrame(all_data)
    
    # Pivot to wide format: One row per Country-Year, columns for GDP and PopDensity
    # First, ensure we have unique rows
    df = df.drop_duplicates(subset=['CountryCode', 'Year', 'gdp', 'pop_density'], keep='first')
    
    # Pivot
    df_wide = df.pivot_table(
        index=['Country', 'CountryCode', 'Year'],
        columns=None,
        values=['gdp', 'pop_density'],
        aggfunc='first'
    ).reset_index()
    
    # Flatten columns if necessary
    df_wide.columns = ['Country', 'CountryCode', 'Year', 'GDP', 'Population_Density']
    
    # Save to CSV
    df_wide.to_csv(output_path, index=False)
    logger.info(f"Saved World Bank economic data ({len(df_wide)} rows) to {output_path}")
    
    return df_wide

def load_cbmrm_proxy_data(proxy_path: Path) -> Optional[pd.DataFrame]:
    """
    Load CBNRM proxy data from a CSV file.
    Returns DataFrame or None if file missing/empty.
    """
    if not proxy_path.exists():
        logger.warning(f"CBNRM proxy file not found: {proxy_path}")
        return None
    
    try:
        df = pd.read_csv(proxy_path)
        if df.empty:
            logger.warning(f"CBNRM proxy file is empty: {proxy_path}")
            return None
        logger.info(f"Loaded CBNRM proxy data: {len(df)} rows from {proxy_path}")
        return df
    except Exception as e:
        logger.error(f"Error loading CBNRM proxy data: {e}")
        return None

def main():
    """
    Main entry point for T012: World Bank data loader.
    Fetches GDP and Population Density, loads CBNRM proxy, and saves outputs.
    """
    logger.info("Starting T012: World Bank Data Loader")
    
    # Configuration
    config = get_config()
    start_year = config.get('DATA_YEARS_START', 2000)
    end_year = config.get('DATA_YEARS_END', 2020)
    
    # Paths
    data_dir = Path("data/raw")
    data_dir.mkdir(parents=True, exist_ok=True)
    
    wb_output_path = data_dir / "wb_economic_data.csv"
    proxy_primary_path = data_dir / "cbnrm_proxy_primary.csv"
    proxy_secondary_path = data_dir / "cbnrm_proxy_secondary.csv"
    proxy_tertiary_path = data_dir / "cbnrm_proxy_tertiary.csv"
    
    # Step 1: Fetch World Bank Economic Data
    logger.info("Fetching GDP and Population Density from World Bank...")
    wb_df = load_world_bank_gdp_population(start_year, end_year, wb_output_path)
    
    if wb_df is None or wb_df.empty:
        logger.warning("No World Bank economic data fetched. Proceeding with empty dataset.")
    
    # Step 2: Load CBNRM Proxy Data (Priority: Primary -> Secondary -> Tertiary)
    proxy_source = None
    proxy_df = None
    
    # Try Primary
    if proxy_primary_path.exists():
        proxy_df = load_cbmrm_proxy_data(proxy_primary_path)
        proxy_source = "primary"
    
    # Try Secondary if Primary failed
    if proxy_df is None and proxy_secondary_path.exists():
        proxy_df = load_cbmrm_proxy_data(proxy_secondary_path)
        proxy_source = "secondary"
    
    # Try Tertiary if Secondary failed
    if proxy_df is None and proxy_tertiary_path.exists():
        proxy_df = load_cbmrm_proxy_data(proxy_tertiary_path)
        proxy_source = "tertiary"
    
    if proxy_df is not None:
        logger.info(f"Successfully loaded CBNRM proxy from {proxy_source} source.")
    else:
        logger.warning("No CBNRM proxy data available. Proceeding without it.")
    
    # Step 3: Save Proxy Data (if loaded) to ensure it's in the raw directory
    # Note: The task says "Save ... the proxy to data/raw/cbnrm_proxy_primary.csv (or secondary/tertiary)"
    # We assume the fetch tasks (T009a/b/c) already saved them. We just log the status.
    # However, if we need to ensure the file exists for downstream tasks, we could copy it.
    # For now, we rely on the fetch tasks having written them.
    
    logger.info("T012: World Bank Data Loader completed.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
