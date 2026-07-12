"""
Data download module for CSAs Food Security research.

This module provides functions to download data from:
- LSMS (Living Standards Measurement Study)
- NASA POWER (climate data)
- FAOSTAT (agricultural statistics)
"""

import os
import json
import time
import requests
from pathlib import Path
from typing import Optional, Dict, List, Any, Union
import logging

from utils.config import get_raw_data_dir, get_target_countries, get_target_years
from utils.logging import initialize_logging

# Initialize logging
logger = logging.getLogger(__name__)
initialize_logging()

# Constants
LSMS_BASE_URL = "https://datatopics.worldbank.org/lsms/"
NASA_POWER_API_URL = "https://power.larc.nasa.gov/api/station/day"
FAOSTAT_BASE_URL = "https://www.fao.org/faostat/en/#data"
FAOSTAT_API_URL = "https://www.fao.org/faostat/api/data/v1"

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

def _ensure_raw_data_dir():
    """Ensure the raw data directory exists."""
    raw_dir = get_raw_data_dir()
    raw_dir.mkdir(parents=True, exist_ok=True)
    return raw_dir

def _retry_request(url, params=None, headers=None, timeout=30):
    """
    Make a request with retry logic.
    
    Args:
        url: The URL to request
        params: Query parameters
        headers: Request headers
        timeout: Request timeout in seconds
        
    Returns:
        Response object if successful, None otherwise
    """
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, params=params, headers=headers, timeout=timeout)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logger.warning(f"Request attempt {attempt + 1} failed: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
            else:
                logger.error(f"All {MAX_RETRIES} attempts failed for {url}")
                return None

def download_lsms(country: str, year: int) -> Optional[Path]:
    """
    Download LSMS (Living Standards Measurement Study) data for a specific country and year.
    
    Args:
        country: Country code or name (e.g., 'KEN' for Kenya, 'IND' for India)
        year: Survey year (e.g., 2021)
        
    Returns:
        Path to the downloaded file if successful, None otherwise
    """
    logger.info(f"Downloading LSMS data for {country} ({year})")
    
    raw_dir = _ensure_raw_data_dir()
    output_path = raw_dir / f"lsms_{country}_{year}.csv"
    
    # Check if file already exists
    if output_path.exists():
        logger.info(f"LSMS data for {country} ({year}) already exists at {output_path}")
        return output_path
    
    # Construct the download URL
    # Note: LSMS data is typically available through specific survey URLs
    # This is a generalized approach; actual URLs may vary by survey
    survey_codes = {
        'KEN': 'kenya_household_consumption',
        'IND': 'india_consumption_expenditure',
        'VNM': 'vietnam_household_living_standards'
    }
    
    survey_code = survey_codes.get(country.upper())
    if not survey_code:
        logger.warning(f"No survey code found for country: {country}")
        # Try a generic search approach
        search_url = f"{LSMS_BASE_URL}search?q={country}&year={year}"
        response = _retry_request(search_url)
        if not response:
            logger.error(f"Could not find LSMS data for {country} ({year})")
            return None
    else:
        # Construct the specific download URL
        download_url = f"{LSMS_BASE_URL}microdata/{survey_code}_{year}/download"
        response = _retry_request(download_url)
    
    if not response:
        logger.error(f"Failed to download LSMS data for {country} ({year})")
        return None
    
    # Save the downloaded data
    try:
        # If the response is a direct file
        if 'application/octet-stream' in response.headers.get('Content-Type', '') or \
           'application/zip' in response.headers.get('Content-Type', '') or \
           'text/csv' in response.headers.get('Content-Type', ''):
            with open(output_path, 'wb') as f:
                f.write(response.content)
            logger.info(f"Successfully downloaded LSMS data to {output_path}")
            return output_path
        else:
            # If the response is HTML or JSON with download links
            logger.warning(f"Unexpected response type for LSMS download: {response.headers.get('Content-Type')}")
            # Save as JSON for further processing
            json_path = raw_dir / f"lsms_{country}_{year}_metadata.json"
            with open(json_path, 'w') as f:
                json.dump(response.json(), f, indent=2)
            logger.info(f"Saved LSMS metadata to {json_path}")
            return None
    except Exception as e:
        logger.error(f"Error saving LSMS data: {e}")
        return None

def download_lsms_batch(countries: List[str], years: List[int]) -> List[Path]:
    """
    Download LSMS data for multiple country-year combinations.
    
    Args:
        countries: List of country codes
        years: List of years
        
    Returns:
        List of paths to downloaded files
    """
    downloaded_files = []
    
    for country in countries:
        for year in years:
            logger.info(f"Processing LSMS download for {country} ({year})")
            result = download_lsms(country, year)
            if result:
                downloaded_files.append(result)
            time.sleep(1)  # Be polite to the server
    
    return downloaded_files

def download_nasa_power(lat: float, lon: float, start: str, end: str) -> Optional[Path]:
    """
    Download climate data from NASA POWER API for a specific location and time period.
    
    Args:
        lat: Latitude of the location
        lon: Longitude of the location
        start: Start date in 'YYYY-MM-DD' format
        end: End date in 'YYYY-MM-DD' format
        
    Returns:
        Path to the downloaded file if successful, None otherwise
    """
    logger.info(f"Downloading NASA POWER data for ({lat}, {lon}) from {start} to {end}")
    
    raw_dir = _ensure_raw_data_dir()
    output_path = raw_dir / f"nasa_power_{lat}_{lon}_{start}_{end}.csv"
    
    # Check if file already exists
    if output_path.exists():
        logger.info(f"NASA POWER data for ({lat}, {lon}) already exists at {output_path}")
        return output_path
    
    # Construct the API request
    params = {
        'latitude': lat,
        'longitude': lon,
        'startDate': start,
        'endDate': end,
        'temporalAverage': 'DAILY',
        'format': 'JSON',
        'parameters': 'T2M,T2M_MAX,T2M_MIN,PSL,WS10M,WD10M,RSNS,RSNSD,RNL,PRECTOT'
    }
    
    response = _retry_request(NASA_POWER_API_URL, params=params)
    
    if not response:
        logger.error(f"Failed to download NASA POWER data for ({lat}, {lon})")
        return None
    
    try:
        data = response.json()
        
        # Extract the data from the response
        if 'properties' in data and 'parameter' in data['properties']:
            # Convert to a more usable format
            import pandas as pd
            
            parameters = data['properties']['parameter']
            dates = list(parameters[next(iter(parameters))].keys())
            
            # Create a DataFrame
            df_data = {'date': dates}
            for param, values in parameters.items():
                df_data[param] = [values.get(d, None) for d in dates]
            
            df = pd.DataFrame(df_data)
            df.to_csv(output_path, index=False)
            
            logger.info(f"Successfully downloaded NASA POWER data to {output_path}")
            return output_path
        else:
            logger.error("Unexpected NASA POWER API response structure")
            return None
    except Exception as e:
        logger.error(f"Error processing NASA POWER response: {e}")
        return None

def download_nasa_power_batch(locations: List[Dict[str, Union[float, str]]]) -> List[Path]:
    """
    Download NASA POWER data for multiple locations and time periods.
    
    Args:
        locations: List of dicts with 'lat', 'lon', 'start', 'end' keys
        
    Returns:
        List of paths to downloaded files
    """
    downloaded_files = []
    
    for loc in locations:
        lat = loc['lat']
        lon = loc['lon']
        start = loc['start']
        end = loc['end']
        
        logger.info(f"Processing NASA POWER download for ({lat}, {lon})")
        result = download_nasa_power(lat, lon, start, end)
        if result:
            downloaded_files.append(result)
        time.sleep(2)  # Be polite to the server
    
    return downloaded_files

def download_faostat(indicator: str) -> Optional[Path]:
    """
    Download agricultural indicator data from FAOSTAT.
    
    Args:
        indicator: FAOSTAT indicator code (e.g., 'FLK' for food loss, 'CND' for crop production)
        
    Returns:
        Path to the downloaded file if successful, None otherwise
    """
    logger.info(f"Downloading FAOSTAT data for indicator: {indicator}")
    
    raw_dir = _ensure_raw_data_dir()
    output_path = raw_dir / f"faostat_{indicator}.csv"
    
    # Check if file already exists
    if output_path.exists():
        logger.info(f"FAOSTAT data for {indicator} already exists at {output_path}")
        return output_path
    
    # FAOSTAT API requires specific parameters
    # We'll download data for target countries and years
    countries = get_target_countries()
    years = get_target_years()
    
    # Construct the API request
    params = {
        'domain': 'CL',  # Climate domain or general
        'element': 'CND',  # Crop production or appropriate element
        'item': indicator,
        'year': ','.join(map(str, years)),
        'area': ','.join(countries),
        'format': 'csv'
    }
    
    # FAOSTAT API might require authentication or have different endpoints
    # This is a generalized approach; actual implementation may vary
    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; CSA-Research-Agent/1.0)'
    }
    
    response = _retry_request(FAOSTAT_API_URL, params=params, headers=headers)
    
    if not response:
        logger.warning(f"Could not download FAOSTAT data for {indicator} via API")
        # Try alternative approach: direct download link
        alt_url = f"{FAOSTAT_BASE_URL}?q={indicator}&download=1"
        response = _retry_request(alt_url, headers=headers)
    
    if not response:
        logger.error(f"Failed to download FAOSTAT data for {indicator}")
        return None
    
    try:
        # Save the CSV data
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        logger.info(f"Successfully downloaded FAOSTAT data to {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"Error saving FAOSTAT data: {e}")
        return None

def download_faostat_batch(indicators: List[str]) -> List[Path]:
    """
    Download multiple FAOSTAT indicators.
    
    Args:
        indicators: List of FAOSTAT indicator codes
        
    Returns:
        List of paths to downloaded files
    """
    downloaded_files = []
    
    for indicator in indicators:
        logger.info(f"Processing FAOSTAT download for {indicator}")
        result = download_faostat(indicator)
        if result:
            downloaded_files.append(result)
        time.sleep(2)  # Be polite to the server
    
    return downloaded_files

def main():
    """
    Main function to demonstrate data download capabilities.
    """
    # Get target countries and years from config
    countries = get_target_countries()
    years = get_target_years()
    
    logger.info(f"Target countries: {countries}")
    logger.info(f"Target years: {years}")
    
    # Example downloads (these would need real data to work)
    # LSMS download example
    if countries and years:
        lsms_results = download_lsms_batch(countries, years)
        logger.info(f"LSMS downloads completed: {len(lsms_results)} files")
    
    # NASA POWER example (using sample coordinates)
    # This would typically use coordinates from the survey data
    sample_locations = [
        {'lat': -1.2921, 'lon': 36.8219, 'start': '2020-01-01', 'end': '2020-12-31'},  # Nairobi
        {'lat': 28.6139, 'lon': 77.2090, 'start': '2020-01-01', 'end': '2020-12-31'},  # Delhi
        {'lat': 21.0285, 'lon': 105.8542, 'start': '2020-01-01', 'end': '2020-12-31'}  # Hanoi
    ]
    
    nasa_results = download_nasa_power_batch(sample_locations)
    logger.info(f"NASA POWER downloads completed: {len(nasa_results)} files")
    
    # FAOSTAT example
    faostat_indicators = ['CND', 'FLK', 'PAG']  # Crop production, Food loss, Agriculture
    faostat_results = download_faostat_batch(faostat_indicators)
    logger.info(f"FAOSTAT downloads completed: {len(faostat_results)} files")
    
    logger.info("All download operations completed")

if __name__ == "__main__":
    main()