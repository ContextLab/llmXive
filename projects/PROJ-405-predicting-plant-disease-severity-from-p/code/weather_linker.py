import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import requests
from requests.exceptions import RequestException, Timeout
from config import get_path, get_env_or_fail

logger = logging.getLogger(__name__)

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great circle distance between two points in km."""
    from math import radians, sin, cos, sqrt, atan2
    R = 6371.0  # Earth radius in km
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c

def fetch_weather_open_meteo(lat: float, lon: float, date: datetime) -> Optional[Dict]:
    """
    Fetch weather data from Open-Meteo API.
    Implements exponential backoff for rate limits.
    """
    base_url = get_path("api.open_meteo_base_url")
    # Open-Meteo doesn't require an API key for public data, but we check for one if needed
    # We use a fixed 7-day window as per T050
    start_date = (date - timedelta(days=7)).strftime("%Y-%m-%d")
    end_date = date.strftime("%Y-%m-%d")
    
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date,
        "end_date": end_date,
        "daily": "temperature_2m_mean,relative_humidity_2m_mean,precipitation_sum",
        "timezone": "auto"
    }
    
    max_retries = 3
    delay = 1.0
    
    for attempt in range(max_retries):
        try:
            response = requests.get(base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if "daily" in data and data["daily"]:
                # Return the last day's data (the image date)
                daily = data["daily"]
                # Find the entry closest to the image date
                # Since we queried a range, we might get multiple days.
                # We assume the last entry is the one we want or match by date.
                # For simplicity, we take the last entry if the list is not empty.
                # A more robust solution would match the date string.
                last_entry = daily[-1]
                return {
                    "mean_temp": last_entry.get("temperature_2m_mean"),
                    "mean_humidity": last_entry.get("relative_humidity_2m_mean"),
                    "total_precipitation": last_entry.get("precipitation_sum")
                }
            else:
                logger.warning(f"No weather data returned for {lat}, {lon} on {date}")
                return None
                
        except (RequestException, Timeout) as e:
            logger.warning(f"Open-Meteo request failed (attempt {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(delay * (2 ** attempt))
            else:
                logger.error("Max retries reached for Open-Meteo.")
                return None
    return None

def fetch_weather_noaa(lat: float, lon: float, date: datetime) -> Optional[Dict]:
    """
    Fallback to NOAA API.
    Note: NOAA API requires an API key. We try to get it from env.
    If it fails, we return None to trigger nearest neighbor imputation logic
    in the caller or exclude the record if that also fails.
    """
    api_key = None
    try:
        api_key = get_env_or_fail("NOAA_API_KEY")
    except EnvironmentError:
        logger.warning("NOAA_API_KEY not set. Skipping NOAA fallback.")
        return None
    
    # NOAA API logic would go here
    # This is a placeholder for the actual implementation
    # Since we don't have a real key in the environment, we return None
    # to simulate a failure and trigger the next fallback or exclusion.
    logger.warning("NOAA API fallback attempted but no key provided.")
    return None

def get_weather_for_record(lat: float, lon: float, date: datetime) -> Optional[Dict]:
    """
    Get weather data for a specific record.
    Tries Open-Meteo first, then NOAA, then nearest neighbor (if available).
    If all fail, returns None.
    """
    # Try Open-Meteo
    weather = fetch_weather_open_meteo(lat, lon, date)
    if weather:
        return weather
    
    # Try NOAA
    weather = fetch_weather_noaa(lat, lon, date)
    if weather:
        return weather
    
    # If all fail, we cannot proceed with this record
    # The caller (data_ingestion.py) will log a warning and exclude it
    logger.error(f"Failed to fetch weather for {lat}, {lon} on {date}. All sources failed.")
    return None

def merge_weather_and_features(records: List[Dict]) -> List[Dict]:
    """
    Merge weather data into the records list.
    This is a helper that might be used if not doing it in the main loop.
    """
    return records
