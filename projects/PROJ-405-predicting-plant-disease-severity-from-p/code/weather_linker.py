"""
Weather Linker Module: Open-Meteo API Integration.

This module implements the fetching of 7-day historical weather data
for specific locations and dates using the Open-Meteo API. It includes
robust exponential backoff for rate limiting and strict error handling
to ensure no synthetic data is generated if the real source is unavailable.
"""
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import requests
from requests.exceptions import RequestException, Timeout

from config import get_path
from utils.logging_config import get_logger

# Constants
OPEN_METEO_API_BASE = "https://api.open-meteo.com/v1"
MAX_RETRIES = 5
INITIAL_BACKOFF = 1.0  # seconds
MAX_BACKOFF = 30.0     # seconds
REQUEST_TIMEOUT = 10   # seconds

logger = get_logger(__name__)


def fetch_historical_weather(
    lat: float,
    lon: float,
    date_start: datetime,
    date_end: datetime,
    max_retries: int = MAX_RETRIES,
    initial_backoff: float = INITIAL_BACKOFF
) -> Dict[str, Any]:
    """
    Fetches 7-day historical weather data from Open-Meteo for a given location and date range.

    Args:
        lat (float): Latitude of the location.
        lon (float): Longitude of the location.
        date_start (datetime): Start date of the historical period.
        date_end (datetime): End date of the historical period.
        max_retries (int): Maximum number of retry attempts with exponential backoff.
        initial_backoff (float): Initial backoff duration in seconds.

    Returns:
        Dict[str, Any]: Parsed weather data containing mean temperature, mean humidity,
                        and total precipitation.

    Raises:
        RuntimeError: If the API fails to return data after max retries or if the
                      response structure is invalid. This ensures the pipeline fails
                      loudly rather than using synthetic data.
        ValueError: If date_end is not after date_start.
    """
    if date_end <= date_start:
        raise ValueError("date_end must be after date_start")

    # Format dates as ISO 8601 strings (YYYY-MM-DD)
    start_str = date_start.strftime("%Y-%m-%d")
    end_str = date_end.strftime("%Y-%m-%d")

    url = f"{OPEN_METEO_API_BASE}/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_str,
        "end_date": end_str,
        "daily": "temperature_2m_mean,relative_humidity_2m_mean,precipitation_sum",
        "timezone": "auto",
        "forecast_days": 1  # We are providing the specific date range, not a forecast
    }

    # Note: Open-Meteo historical endpoint is the same as forecast endpoint for past dates
    # if the date is in the past. The API handles the logic.
    
    attempt = 0
    backoff = initial_backoff

    while attempt < max_retries:
        try:
            logger.debug(f"Fetching weather for {lat}, {lon} from {start_str} to {end_str} (Attempt {attempt + 1}/{max_retries})")
            response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
            
            if response.status_code == 200:
                data = response.json()
                if "daily" in data and len(data["daily"]["time"]) > 0:
                    return _parse_weather_response(data)
                else:
                    raise RuntimeError("Open-Meteo returned valid JSON but no daily data found.")
            
            elif response.status_code == 429:
                # Rate limit exceeded
                logger.warning(f"Rate limit exceeded (429). Retrying in {backoff:.2f}s...")
                time.sleep(backoff)
                attempt += 1
                backoff = min(backoff * 2, MAX_BACKOFF)
                continue
            
            elif response.status_code >= 500:
                # Server error, retry
                logger.warning(f"Server error {response.status_code}. Retrying in {backoff:.2f}s...")
                time.sleep(backoff)
                attempt += 1
                backoff = min(backoff * 2, MAX_BACKOFF)
                continue
            
            else:
                # Client error (4xx) that is not 429, usually indicates bad request or invalid location
                logger.error(f"API Error {response.status_code}: {response.text}")
                raise RuntimeError(f"Open-Meteo API failed with status {response.status_code}: {response.text}")

        except Timeout:
            logger.warning("Request timed out. Retrying...")
            attempt += 1
            time.sleep(backoff)
            backoff = min(backoff * 2, MAX_BACKOFF)
        
        except RequestException as e:
            logger.warning(f"Network error: {e}. Retrying...")
            attempt += 1
            time.sleep(backoff)
            backoff = min(backoff * 2, MAX_BACKOFF)

    # If we exit the loop, all retries failed
    raise RuntimeError(
        f"Failed to fetch weather data for ({lat}, {lon}) after {max_retries} attempts. "
        f"Aborting to prevent synthetic data fallback."
    )


def _parse_weather_response(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parses the Open-Meteo JSON response into a standardized dictionary.

    Args:
        data (Dict[str, Any]): The raw JSON response from Open-Meteo.

    Returns:
        Dict[str, Any]: Aggregated weather metrics.
    """
    daily = data["daily"]
    
    # Open-Meteo returns lists for daily data. We expect the list to match the date range.
    # We aggregate (mean/sum) across the requested range if multiple days are requested,
    # or return the single day's values if only one day is requested.
    # The task specifies "7-day historical weather", so we aggregate over the list.
    
    temps = daily.get("temperature_2m_mean", [])
    humidities = daily.get("relative_humidity_2m_mean", [])
    precipitations = daily.get("precipitation_sum", [])
    
    if not temps or not humidities or not precipitations:
        raise ValueError("Incomplete weather data returned from API.")

    # Calculate aggregates
    mean_temp = sum(temps) / len(temps)
    mean_humidity = sum(humidities) / len(humidities)
    total_precipitation = sum(precipitations)
    
    return {
        "mean_temp": mean_temp,
        "mean_humidity": mean_humidity,
        "total_precipitation": total_precipitation,
        "data_points": len(temps)
    }


def get_weather_for_record(
    lat: float,
    lon: float,
    image_date: datetime,
    days_back: int = 7
) -> Optional[Dict[str, Any]]:
    """
    Wrapper to fetch weather for a specific image record.
    
    Calculates the 7-day window ending on the image date and fetches data.
    
    Args:
        lat (float): Latitude.
        lon (float): Longitude.
        image_date (datetime): The date the image was taken.
        days_back (int): Number of days to look back (default 7).
    
    Returns:
        Dict[str, Any] or None: Weather data if successful, None if excluded (though
                                 this function is designed to raise on failure per constraints).
    """
    date_end = image_date
    date_start = image_date - timedelta(days=days_back - 1)
    
    try:
        return fetch_historical_weather(lat, lon, date_start, date_end)
    except Exception as e:
        # Log the failure but do not return None to avoid silent failures in the pipeline.
        # The caller (data ingestion) should handle the exception to exclude the record.
        logger.error(f"Failed to retrieve weather for image at {image_date} ({lat}, {lon}): {e}")
        raise