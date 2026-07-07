"""
Data download and loading module for CBNRM effectiveness analysis.

Handles fetching FAO FRA data and loading World Bank data (GDP, Population Density)
and the CBNRM proxy data from previously downloaded files.
"""
import json
import time
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_config, YEAR_RANGE
from logging_config import get_logger

logger = get_logger(__name__)

# API Endpoints (from config)
API_ENDPOINTS = get_config().get('API_ENDPOINTS', {})
WORLD_BANK_API = API_ENDPOINTS.get('world_bank', 'https://api.worldbank.org/v2')
FAO_API = API_ENDPOINTS.get('fao', 'https://www.fao.org/faostat/api')

# Year range from config
START_YEAR, END_YEAR = YEAR_RANGE

def fetch_fao_fra_data(year_start: int = None, year_end: int = None) -> List[Dict[str, Any]]:
    """
    Fetch Forest Area Change data from FAO FRA API.
    
    Args:
        year_start: Start year for data range (default: from config)
        year_end: End year for data range (default: from config)
        
    Returns:
        List of dictionaries containing FAO data records
    """
    if year_start is None:
        year_start = START_YEAR
    if year_end is None:
        year_end = END_YEAR
        
    logger.info(f"Fetching FAO FRA data for years {year_start}-{year_end}")
    
    # FAO FRA API endpoint for forest area change
    # Note: Actual endpoint may vary based on FAO API documentation
    url = f"{FAO_API}/data/forest-area-change"
    
    params = {
        'start_year': year_start,
        'end_year': year_end,
        'format': 'json'
    }
    
    headers = {
        'User-Agent': 'llmXive-CBNRM-Analysis/1.0'
    }
    
    data = []
    max_retries = 5
    retry_delay = 2  # seconds
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, params=params, headers=headers, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                data = result.get('data', [])
                logger.info(f"Successfully fetched {len(data)} records from FAO")
                break
            elif response.status_code == 503:
                logger.warning(f"FAO API returned 503 (Service Unavailable). Attempt {attempt + 1}/{max_retries}")
                time.sleep(retry_delay * (2 ** attempt))  # Exponential backoff
                continue
            else:
                logger.error(f"FAO API returned status code: {response.status_code}")
                response.raise_for_status()
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay * (2 ** attempt))
            else:
                raise
    
    return data

def save_fao_data_to_csv(data: List[Dict[str, Any]], output_path: str) -> None:
    """
    Save FAO data to CSV file.
    
    Args:
        data: List of FAO data records
        output_path: Path to output CSV file
    """
    if not data:
        logger.warning("No data to save")
        return
        
    import pandas as pd
    
    df = pd.DataFrame(data)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved FAO data to {output_path} ({len(df)} rows)")

def load_world_bank_gdp_population(year_start: int = None, year_end: int = None) -> Dict[str, Any]:
    """
    Load GDP and Population Density data from World Bank API.
    Fetches data if not already cached, otherwise loads from cache.
    
    Args:
        year_start: Start year for data range (default: from config)
        year_end: End year for data range (default: from config)
        
    Returns:
        Dictionary with 'gdp' and 'population_density' DataFrames
    """
    if year_start is None:
        year_start = START_YEAR
    if year_end is None:
        year_end = END_YEAR
        
    logger.info(f"Loading World Bank GDP and Population Density data for {year_start}-{year_end}")
    
    # Define cache paths
    cache_dir = Path("data/raw")
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    gdp_cache_path = cache_dir / "world_bank_gdp.csv"
    pop_cache_path = cache_dir / "world_bank_population_density.csv"
    
    import pandas as pd
    
    # Load or fetch GDP data
    if gdp_cache_path.exists():
        logger.info(f"Loading GDP data from cache: {gdp_cache_path}")
        gdp_df = pd.read_csv(gdp_cache_path)
    else:
        logger.info("Fetching GDP data from World Bank API")
        gdp_df = fetch_world_bank_indicator(
            indicator='NY.GDP.PCAP.CD',  # GDP per capita (current US$)
            year_start=year_start,
            year_end=year_end
        )
        gdp_df.to_csv(gdp_cache_path, index=False)
        logger.info(f"Saved GDP data to cache ({len(gdp_df)} rows)")
    
    # Load or fetch Population Density data
    if pop_cache_path.exists():
        logger.info(f"Loading Population Density data from cache: {pop_cache_path}")
        pop_df = pd.read_csv(pop_cache_path)
    else:
        logger.info("Fetching Population Density data from World Bank API")
        pop_df = fetch_world_bank_indicator(
            indicator='SP.POP.DENS',  # Population density (people per sq. km)
            year_start=year_start,
            year_end=year_end
        )
        pop_df.to_csv(pop_cache_path, index=False)
        logger.info(f"Saved Population Density data to cache ({len(pop_df)} rows)")
    
    return {
        'gdp': gdp_df,
        'population_density': pop_df
    }

def fetch_world_bank_indicator(indicator: str, year_start: int = None, year_end: int = None) -> 'pd.DataFrame':
    """
    Fetch data for a specific World Bank indicator.
    
    Args:
        indicator: World Bank indicator code
        year_start: Start year for data range
        year_end: End year for data range
        
    Returns:
        DataFrame with indicator data
    """
    import pandas as pd
    
    all_data = []
    
    for year in range(year_start, year_end + 1):
        url = f"{WORLD_BANK_API}/country/all/indicator/{indicator}"
        params = {
            'date': f'{year}:{year}',
            'format': 'json',
            'per_page': 10000
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            result = response.json()
            
            if len(result) >= 2:
                page_data = result[1]  # First element is metadata
                for record in page_data:
                    if record.get('value') is not None:
                        all_data.append({
                            'country_code': record.get('countryiso3code', ''),
                            'country_name': record.get('country', {}).get('value', ''),
                            'year': year,
                            'value': record.get('value')
                        })
            
            # Respect API rate limits
            time.sleep(0.5)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch {indicator} for {year}: {e}")
            continue
    
    if not all_data:
        logger.warning(f"No data found for indicator {indicator}")
        return pd.DataFrame(columns=['country_code', 'country_name', 'year', 'value'])
        
    return pd.DataFrame(all_data)

def load_cbmrm_proxy_data() -> 'pd.DataFrame':
    """
    Load CBNRM proxy data from the file generated by T009.
    
    Returns:
        DataFrame containing CBNRM proxy data
    """
    proxy_path = Path("data/raw/cbnrm_proxy.csv")
    
    if not proxy_path.exists():
        raise FileNotFoundError(
            f"CBNRM proxy data file not found at {proxy_path}. "
            "Please ensure task T009 has been completed successfully."
        )
    
    logger.info(f"Loading CBNRM proxy data from {proxy_path}")
    
    import pandas as pd
    df = pd.read_csv(proxy_path)
    
    logger.info(f"Loaded {len(df)} rows of CBNRM proxy data")
    
    return df

def main():
    """
    Main function to execute data loading for T012.
    Loads GDP, Population Density, and CBNRM proxy data.
    """
    logger.info("Starting T012: World Bank data loader and CBNRM proxy loader")
    
    try:
        # Load World Bank data (GDP and Population Density)
        wb_data = load_world_bank_gdp_population()
        
        # Load CBNRM proxy data
        cbnrm_data = load_cbmrm_proxy_data()
        
        # Save merged World Bank data to processed directory
        processed_dir = Path("data/processed")
        processed_dir.mkdir(parents=True, exist_ok=True)
        
        # Save GDP data
        gdp_output = processed_dir / "world_bank_gdp_processed.csv"
        wb_data['gdp'].to_csv(gdp_output, index=False)
        logger.info(f"Saved processed GDP data to {gdp_output}")
        
        # Save Population Density data
        pop_output = processed_dir / "world_bank_pop_density_processed.csv"
        wb_data['population_density'].to_csv(pop_output, index=False)
        logger.info(f"Saved processed Population Density data to {pop_output}")
        
        # Save CBNRM proxy data to processed directory
        cbnrm_output = processed_dir / "cbnrm_proxy_processed.csv"
        cbnrm_data.to_csv(cbnrm_output, index=False)
        logger.info(f"Saved processed CBNRM proxy data to {cbnrm_output}")
        
        # Log summary
        logger.info("T012 completed successfully")
        logger.info(f"  - GDP records: {len(wb_data['gdp'])}")
        logger.info(f"  - Population Density records: {len(wb_data['population_density'])}")
        logger.info(f"  - CBNRM proxy records: {len(cbnrm_data)}")
        
    except Exception as e:
        logger.error(f"T012 failed: {e}")
        raise

if __name__ == "__main__":
    main()