"""Data download module for LSMS, NASA POWER, and FAOSTAT."""
import os
import json
import time
import requests
from pathlib import Path
from typing import Optional, Dict, List, Any, Union
from utils.logging import initialize_logging

# Initialize logger (tolerant of all call shapes)
logger = initialize_logging()

TARGET_COUNTRIES = ["KEN", "IND", "VNM"]
TARGET_YEARS = [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022]

def download_lsms(country: str, year: int) -> Optional[Path]:
    """Download LSMS data for a specific country and year.
    
    Args:
        country: ISO 3-letter country code.
        year: Year of the survey.
    
    Returns:
        Path to the downloaded file, or None if not found.
    """
    # Placeholder for LSMS download logic
    # In a real implementation, this would fetch from the World Bank LSMS API
    logger.log("download_lsms", country=country, year=year, status="placeholder")
    return None

def download_lsms_batch(countries: List[str], years: List[int]) -> List[Path]:
    """Download LSMS data for multiple countries and years."""
    results = []
    for country in countries:
        for year in years:
            path = download_lsms(country, year)
            if path:
                results.append(path)
    return results

def _get_nearest_power_station(lat: float, lon: float) -> Dict[str, Any]:
    """Find the nearest NASA POWER station to a given coordinate.
    
    Args:
        lat: Latitude.
        lon: Longitude.
    
    Returns:
        Dictionary with station info.
    """
    # Simplified: In reality, NASA POWER provides data for a grid, not stations.
    # We will use the grid point closest to the given coordinate.
    # For this implementation, we'll assume the grid point is the same as the input.
    return {"lat": lat, "lon": lon}

def download_nasa_power(lat: float, lon: float, start: str, end: str) -> Optional[Dict[str, Any]]:
    """Download climate data from NASA POWER for a given location and date range.
    
    Args:
        lat: Latitude.
        lon: Longitude.
        start: Start date in 'YYYY-MM-DD' format.
        end: End date in 'YYYY-MM-DD' format.
    
    Returns:
        Dictionary with climate data, or None if failed.
    """
    # NASA POWER API endpoint
    url = "https://power.larc.nasa.gov/api/temporal/daily/point"
    
    params = {
        "community": "RE",
        "longitude": str(lon),
        "latitude": str(lat),
        "start": start,
        "end": end,
        "format": "JSON",
        "parameters": "ALLSKY_SFC_SW_DWN,T2M,PRECTOTCORR"
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # Extract the daily data
        if "properties" in data and "parameter" in data["properties"]:
            return data["properties"]["parameter"]
        else:
            logger.log("download_nasa_power_error", lat=lat, lon=lon, reason="Invalid response structure")
            return None
    except requests.exceptions.RequestException as e:
        logger.log("download_nasa_power_error", lat=lat, lon=lon, reason=str(e))
        return None

def _interpolate_gaps(data: Dict[str, Any], max_gap_months: int = 3) -> Dict[str, Any]:
    """Interpolate gaps in climate data if they are <= max_gap_months.
    
    Args:
        data: Climate data dictionary from NASA POWER.
        max_gap_months: Maximum gap size in months to interpolate.
    
    Returns:
        Interpolated data dictionary.
    """
    # Simplified interpolation logic
    # In a real implementation, this would use linear interpolation or similar
    logger.log("interpolate_gaps", max_gap_months=max_gap_months, status="placeholder")
    return data

def download_nasa_power_batch(locations: List[Dict[str, Union[float, str]]], start: str, end: str) -> List[Dict[str, Any]]:
    """Download climate data for multiple locations.
    
    Args:
        locations: List of dictionaries with 'lat' and 'lon' keys.
        start: Start date.
        end: End date.
    
    Returns:
        List of climate data dictionaries.
    """
    results = []
    for loc in locations:
        data = download_nasa_power(loc["lat"], loc["lon"], start, end)
        if data:
            # Interpolate gaps if necessary
            data = _interpolate_gaps(data, max_gap_months=3)
            results.append(data)
    return results

def download_faostat(indicator: str, countries: List[str] = None) -> Optional[Path]:
    """Download FAOSTAT data for a specific indicator.
    
    This implementation uses the FAOSTAT API to fetch data for the specified
    indicator and countries. If countries is None, it defaults to TARGET_COUNTRIES.
    
    Args:
        indicator: FAOSTAT indicator code (e.g., 'CLO' for Cereal Yield).
        countries: List of ISO 3-letter country codes.
    
    Returns:
        Path to the downloaded CSV file, or None if failed.
    """
    if countries is None:
        countries = TARGET_COUNTRIES
    
    base_url = "https://www.fao.org/faostat/en/#data"
    # FAOSTAT API endpoint for bulk download (requires specific parameters)
    # We use the REST API for programmatic access
    api_url = "https://faostat3.fao.org/download/E/EI/en"
    
    # Construct the download request
    # Note: FAOSTAT API often requires a specific payload format
    # We will attempt a direct download using the indicator and country codes
    
    # Prepare the download parameters
    params = {
        "type": "indicator",
        "code": indicator,
        "countries": ",".join(countries),
        "format": "csv"
    }
    
    # Since FAOSTAT's direct API is complex and often requires session handling,
    # we will use a workaround by constructing a specific download URL
    # This is a common pattern for FAOSTAT data retrieval
    download_url = f"https://faostat3.fao.org/download/E/EI/en?code={indicator}&countries={','.join(countries)}&format=csv"
    
    try:
        response = requests.get(download_url, timeout=60)
        response.raise_for_status()
        
        # Ensure the content is CSV
        if "text/csv" in response.headers.get("Content-Type", ""):
            # Create output directory if it doesn't exist
            output_dir = Path("data/raw/faostat")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Save the file with a descriptive name
            safe_indicator = indicator.replace("/", "_").replace(" ", "_")
            safe_countries = "_".join(countries)
            filename = f"faostat_{safe_indicator}_{safe_countries}_{int(time.time())}.csv"
            output_path = output_dir / filename
            
            with open(output_path, "wb") as f:
                f.write(response.content)
            
            logger.log("download_faostat_success", indicator=indicator, countries=countries, path=str(output_path))
            return output_path
        else:
            logger.log("download_faostat_error", indicator=indicator, reason="Invalid content type", status_code=response.status_code)
            return None
            
    except requests.exceptions.RequestException as e:
        logger.log("download_faostat_error", indicator=indicator, countries=countries, reason=str(e))
        return None
    except Exception as e:
        logger.log("download_faostat_error", indicator=indicator, reason=f"Unexpected error: {str(e)}")
        return None

def download_faostat_batch(indicators: List[str], countries: List[str] = None) -> List[Path]:
    """Download FAOSTAT data for multiple indicators.
    
    Args:
        indicators: List of FAOSTAT indicator codes.
        countries: List of country codes.
    
    Returns:
        List of paths to downloaded CSV files.
    """
    results = []
    for indicator in indicators:
        path = download_faostat(indicator, countries)
        if path:
            results.append(path)
    return results

def main():
    """Main entry point for the download module."""
    logger.log("download_module_main", status="started")
    # Example: Download data for Kenya, 2020
    # lsms_data = download_lsms("KEN", 2020)
    # climate_data = download_nasa_power(-1.2921, 36.8219, "2020-01-01", "2020-12-31")
    
    # Example: Download FAOSTAT data for Cereal Yield
    # faostat_data = download_faostat("CLO", ["KEN", "IND", "VNM"])
    
    logger.log("download_module_main", status="completed")

if __name__ == "__main__":
    main()
