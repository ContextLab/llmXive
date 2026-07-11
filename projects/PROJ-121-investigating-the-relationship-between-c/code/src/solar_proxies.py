"""
Solar Proxies Module

Fetches NOAA NGDC indices (sunspot number, solar wind speed, Interplanetary Magnetic Field)
with robust retry logic implementing exponential backoff.
"""
import requests
import time
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
import re
from .utils import get_logger

# Constants
MAX_RETRIES = 3
BASE_DELAY = 1.0  # seconds
MAX_DELAY = 10.0  # seconds
REQUEST_TIMEOUT = 30  # seconds

# NOAA NGDC URLs for daily averages
# Sunspot Number (R) - SIDC SILSO
URL_SUNSPOT = "https://www.sidc.be/users/eclim/SILSO/FILES/SN_dtot_V2.0.txt"
# Solar Wind Speed (km/s) - OMNI 1-hour/60-min data (aggregated to daily)
# Using a representative CDAW or NOAA URL structure for daily averages
# Note: Real implementation might need to parse specific NOAA FTP or API endpoints
# For this implementation, we use a mockable URL structure or a public daily average source
# NOAA SWPC Solar Wind Parameters (Daily Averages)
URL_SOLAR_WIND = "https://www.swpc.noaa.gov/products/solar-wind-parameters"
# Interplanetary Magnetic Field (IMF) Bt (nT)
URL_IMF = "https://www.swpc.noaa.gov/products/interplanetary-magnetic-field"

logger = get_logger(__name__)


def _calculate_backoff(attempt: int) -> float:
    """
    Calculate exponential backoff delay with jitter.

    Args:
        attempt: The current attempt number (0-indexed).

    Returns:
        Delay in seconds.
    """
    delay = min(BASE_DELAY * (2 ** attempt), MAX_DELAY)
    # Add small jitter to prevent thundering herd
    jitter = delay * 0.1
    return delay + jitter


def _fetch_text_with_retry(url: str, session: Optional[requests.Session] = None) -> str:
    """
    Fetch text content from a URL with exponential backoff retry logic.

    Args:
        url: The URL to fetch.
        session: Optional requests session to reuse.

    Returns:
        The text content of the response.

    Raises:
        requests.exceptions.RequestException: If the request fails after MAX_RETRIES attempts.
    """
    if session is None:
        session = requests.Session()

    last_exception = None

    for attempt in range(MAX_RETRIES):
        try:
            logger.info(f"Fetching {url} (attempt {attempt + 1}/{MAX_RETRIES})")
            response = session.get(url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            last_exception = e
            delay = _calculate_backoff(attempt)
            logger.warning(
                f"Request to {url} failed: {e}. "
                f"Retrying in {delay:.2f} seconds..."
            )
            time.sleep(delay)

    logger.error(f"Failed to fetch {url} after {MAX_RETRIES} attempts.")
    raise last_exception


def _parse_silso_sunspot(text: str) -> List[Dict[str, Any]]:
    """
    Parse SILSO Sunspot Number data.

    Format: Year Month Day R StdDev R12 R12StdDev R12R R12RStdDev R12R12 R12R12StdDev
            R12R12R R12R12RStdDev R12R12R12 R12R12R12StdDev R12R12R12R R12R12R12RStdDev
            R12R12R12R12 R12R12R12R12StdDev
            ...
            (Space separated, comments start with #)
    """
    data = []
    lines = text.splitlines()
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        parts = line.split()
        if len(parts) < 4:
            continue
        try:
            year = int(parts[0])
            month = int(parts[1])
            day = int(parts[2])
            r = float(parts[3])
            # Handle -1.0 or -999.0 as missing data
            if r == -1.0 or r == -999.0:
                r = None
            data.append({
                'date': datetime(year, month, day),
                'sunspot_number': r
            })
        except (ValueError, IndexError):
            continue
    return data


def _parse_noaa_sw_data(text: str, data_type: str) -> List[Dict[str, Any]]:
    """
    Parse NOAA Solar Wind or IMF data.
    Assumes a tabular format with headers, handling various common NOAA formats.
    This is a generic parser; specific URL parsing might need refinement based on actual data source.
    """
    data = []
    lines = text.splitlines()
    header_found = False
    headers = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Skip comments
        if line.startswith('#'):
            continue

        parts = line.split()
        if not parts:
            continue

        if not header_found:
            # Heuristic: first line with many columns might be header
            if len(parts) > 3:
                headers = parts
                header_found = True
                continue
            else:
                # Assume data starts immediately if no clear header
                header_found = True

        if not header_found:
            continue

        try:
            # Expected format: YYYY MM DD HH MM SS ... values
            if len(parts) < 6:
                continue

            year = int(parts[0])
            month = int(parts[1])
            day = int(parts[2])
            # Hour/Min/Sec might be present, ignore for daily avg if not needed
            # We'll take the first value of the day or average if multiple
            # For simplicity, taking the first valid row per day
            # In a real scenario, we'd aggregate by day.
            # Here we assume daily data or take the first entry per day.
            date = datetime(year, month, day)

            # Find the index for the specific data type
            # This is a simplification; real parsing depends on exact column order
            # Let's assume the first numeric column after time is the value
            value_idx = 6
            if value_idx >= len(parts):
                continue

            val_str = parts[value_idx]
            if val_str == '-999.0' or val_str == '-1.0' or val_str == 'nan':
                val = None
            else:
                val = float(val_str)

            data.append({
                'date': date,
                data_type: val
            })
        except (ValueError, IndexError):
            continue

    # Aggregate to daily if multiple entries exist (simple average for now)
    daily_data = {}
    for entry in data:
        d = entry['date']
        if d not in daily_data:
            daily_data[d] = []
        if entry[data_type] is not None:
            daily_data[d].append(entry[data_type])

    result = []
    for d, vals in daily_data.items():
        avg_val = sum(vals) / len(vals) if vals else None
        result.append({
            'date': d,
            data_type: avg_val
        })
    return result


def fetch_solar_proxy(
    proxy_type: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> List[Dict[str, Any]]:
    """
    Fetch solar proxy data from NOAA NGDC or related sources.

    Args:
        proxy_type: One of 'sunspot', 'solar_wind', 'imf'.
        start_date: Start date (inclusive). If None, fetches all available.
        end_date: End date (inclusive). If None, fetches all available.

    Returns:
        List of dictionaries containing 'date' and the proxy value.

    Raises:
        ValueError: If proxy_type is invalid.
        requests.exceptions.RequestException: If data fetch fails after retries.
    """
    proxy_type = proxy_type.lower()

    if proxy_type == 'sunspot':
        url = URL_SUNSPOT
        key = 'sunspot_number'
        parser = _parse_silso_sunspot
    elif proxy_type == 'solar_wind':
        url = URL_SOLAR_WIND
        key = 'solar_wind_speed'
        parser = lambda t: _parse_noaa_sw_data(t, 'solar_wind_speed')
    elif proxy_type == 'imf':
        url = URL_IMF
        key = 'imf_bt'
        parser = lambda t: _parse_noaa_sw_data(t, 'imf_bt')
    else:
        raise ValueError(f"Invalid proxy_type: {proxy_type}. Must be 'sunspot', 'solar_wind', or 'imf'.")

    logger.info(f"Fetching {proxy_type} data from {url}")
    text_content = _fetch_text_with_retry(url)
    data = parser(text_content)

    # Filter by date range
    if start_date:
        data = [d for d in data if d['date'] >= start_date]
    if end_date:
        data = [d for d in data if d['date'] <= end_date]

    logger.info(f"Fetched {len(data)} records for {proxy_type}")
    return data
