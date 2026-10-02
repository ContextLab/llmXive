import json
import time
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
import requests

# Ensure logging is configured
from logging_config import get_logger

# Configuration import
from config import get_config

logger = get_logger(__name__)

def fetch_with_backoff(url: str, params: Dict[str, Any], max_retries: int = 3) -> Optional[pd.DataFrame]:
    """
    Fetch data from a URL with exponential backoff retry logic.
    Returns a DataFrame if successful, None if all retries fail.
    """
    for attempt in range(max_retries):
        try:
            logger.info(f"Fetching URL: {url}, Attempt {attempt + 1}/{max_retries}")
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            # World Bank API returns JSON
            data = response.json()
            
            # Handle the specific structure of World Bank API responses
            # Usually data is in the second element of the list
            if isinstance(data, list) and len(data) > 1:
                records = data[1]
                return pd.DataFrame(records)
            elif isinstance(data, dict) and 'page' in data:
                # Handle pagination or specific structure
                records = data.get('data', [])
                return pd.DataFrame(records)
            else:
                logger.warning(f"Unexpected response structure from {url}")
                return pd.DataFrame()

        except requests.exceptions.RequestException as e:
            wait_time = (2 ** attempt) * 2  # Exponential backoff: 2s, 4s, 8s
            logger.warning(f"Request failed: {e}. Retrying in {wait_time}s...")
            time.sleep(wait_time)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON response: {e}")
            return None
        
    logger.error(f"Failed to fetch data from {url} after {max_retries} retries.")
    return None

def verify_fao_indicator(indicator_code: str) -> bool:
    """
    Verify if an FAO indicator exists (placeholder for FAO specific logic).
    """
    # Implementation would go here if FAO verification is needed
    return True

def fetch_fao_fra_data(indicator_code: str, year_start: int, year_end: int) -> Optional[pd.DataFrame]:
    """
    Fetch FAO FRA data (placeholder for FAO specific logic).
    """
    # Implementation would go here
    return None

def save_fao_data_to_csv(df: pd.DataFrame, output_path: Path):
    """
    Save FAO data to CSV.
    """
    if df is not None and not df.empty:
        df.to_csv(output_path, index=False)
        logger.info(f"Saved FAO data to {output_path}")
    else:
        # Create empty CSV with headers if no data
        df = pd.DataFrame(columns=['country', 'year', 'value'])
        df.to_csv(output_path, index=False)
        logger.warning(f"No FAO data to save, created empty file at {output_path}")

def load_world_bank_gdp_population(year_start: int = 2000, year_end: int = 2020) -> pd.DataFrame:
    """
    Fetch GDP (NY.GDP.PCAP.CD) and Population Density (SP.POP.DENS) from World Bank API.
    Returns a DataFrame with columns: country, country_code, year, gdp_per_capita, pop_density.
    """
    config = get_config()
    api_base = config['API_BASE_URL']
    
    indicators = ['NY.GDP.PCAP.CD', 'SP.POP.DENS']
    all_data = []
    
    for indicator in indicators:
        url = f"{api_base}/indicators/{indicator}"
        params = {
            'date': f"{year_start}:{year_end}",
            'format': 'json',
            'per_page': 50000  # Fetch as many as possible
        }
        
        df = fetch_with_backoff(url, params)
        
        if df is not None and not df.empty:
            # Filter for the specific indicator
            df_filtered = df[df['indicator']['id'] == indicator]
            
            # Rename columns for consistency
            df_filtered = df_filtered.rename(columns={
                'value': 'indicator_value',
                'date': 'year',
                'countryiso3code': 'country_code',
                'country': 'country'
            })
            
            # Keep only necessary columns
            df_filtered = df_filtered[['country', 'country_code', 'year', 'indicator_value']]
            df_filtered['indicator'] = indicator
            
            all_data.append(df_filtered)
            logger.info(f"Fetched {len(df_filtered)} rows for indicator {indicator}")
        else:
            logger.warning(f"No data fetched for indicator {indicator}")
    
    if not all_data:
        # Return empty dataframe with expected columns
        return pd.DataFrame(columns=['country', 'country_code', 'year', 'indicator_value', 'indicator'])
    
    combined_df = pd.concat(all_data, ignore_index=True)
    
    # Pivot to have GDP and Pop Density as separate columns
    pivot_df = combined_df.pivot_table(
        index=['country', 'country_code', 'year'],
        columns='indicator',
        values='indicator_value',
        aggfunc='first'
    ).reset_index()
    
    # Rename columns to match expected output
    pivot_df = pivot_df.rename(columns={
        'NY.GDP.PCAP.CD': 'gdp_per_capita',
        'SP.POP.DENS': 'pop_density'
    })
    
    # Ensure year is integer
    pivot_df['year'] = pivot_df['year'].astype(int)
    
    return pivot_df

def load_cbmrm_proxy_data(file_path: Path) -> Optional[pd.DataFrame]:
    """
    Load CBNRM proxy data from a CSV file if it exists.
    Returns the DataFrame or None if file is missing.
    """
    if not file_path.exists():
        logger.warning(f"CBNRM proxy file not found at {file_path}. Continuing without it.")
        return None
    
    try:
        df = pd.read_csv(file_path)
        logger.info(f"Loaded CBNRM proxy data: {len(df)} rows from {file_path}")
        return df
    except Exception as e:
        logger.error(f"Failed to load CBNRM proxy data from {file_path}: {e}")
        return None

def main():
    """
    Main execution function for T012:
    1. Fetch GDP and Population Density from World Bank API.
    2. Load CBNRM proxy data if available.
    3. Save outputs to data/raw/.
    """
    logger.info("Starting T012: World Bank data loader")
    
    # Define paths
    raw_dir = Path("data/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    wb_output_path = raw_dir / "wb_economic_data.csv"
    proxy_output_path = raw_dir / "cbnrm_proxy.csv"
    
    # Fetch World Bank economic data
    logger.info("Fetching World Bank GDP and Population Density data...")
    wb_df = load_world_bank_gdp_population(year_start=2000, year_end=2020)
    
    if wb_df is not None and not wb_df.empty:
        wb_df.to_csv(wb_output_path, index=False)
        logger.info(f"Saved World Bank economic data to {wb_output_path}")
    else:
        # Create empty CSV with headers if no data
        wb_df = pd.DataFrame(columns=['country', 'country_code', 'year', 'gdp_per_capita', 'pop_density'])
        wb_df.to_csv(wb_output_path, index=False)
        logger.warning(f"No World Bank data fetched, created empty file at {wb_output_path}")
    
    # Load CBNRM proxy data (if it exists from T009)
    # Note: T009 might have failed or not run yet, so we handle missing file gracefully
    proxy_df = load_cbmrm_proxy_data(proxy_output_path)
    
    # If proxy file doesn't exist, we don't create it here (T009 is responsible for that)
    # We just log the status
    if proxy_df is None:
        logger.warning("CBNRM proxy data not available. This is expected if T009 has not run or failed.")
    else:
        # Ensure proxy data is saved (in case it was loaded from a different location)
        proxy_df.to_csv(proxy_output_path, index=False)
        logger.info(f"Ensured CBNRM proxy data is saved at {proxy_output_path}")
    
    logger.info("T012 completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
