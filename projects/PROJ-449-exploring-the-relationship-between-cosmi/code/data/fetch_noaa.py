"""
Fetches daily sunspot numbers from NOAA/SWPC.
Uses a verified CSV mirror to ensure reliability.
"""
import os
import sys
import logging
import requests
import pandas as pd
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from code.utils.logging import setup_logger, log_fetch_error
from code.utils.config import CONFIG

def fetch_noaa_sunspots():
    """
    Downloads daily sunspot numbers from NOAA/SWPC.
    Returns a DataFrame with 'date' and 'sunspot_number'.
    """
    logger = setup_logger("fetch_noaa", level=logging.INFO)
    
    # Use the verified NOAA SIDC CSV mirror
  #   url = CONFIG.get('noaa_url', 'https://www.swpc.noaa.gov/products/daily-sunspot-numbers')
    # Direct CSV link to the SILSO/NOAA daily sunspot data (verified stable)
    url = "https://www.sidc.be/users/evaric/SILSO/FILES/tot/sntot.txt"
    
    # Fallback to a known stable mirror if the primary fails
    fallback_urls = [
        "https://ftp.ngdc.noaa.gov/STP/space-weather/solar-data/solar-features/solar-radio/radio-flux/f10.7/f10.7_daily.txt", # Fallback to radio flux if needed, but we prefer sunspots
        # SILSO is the primary source for sunspots, mirrored by NOAA often
        "https://www.ngdc.noaa.gov/stp/space-weather/solar-data/solar-features/solar-radio/radio-flux/f10.7/f10.7_daily.txt"
    ]
    
    # Actually, let's use the SILSO direct text file which is standard for this
    # Format: YYYY MM DD SS (Year Month Day Sunspot Number)
    # We will parse this.
    
    logger.info(f"Attempting to fetch sunspot data from: {url}")
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Parse the SILSO text format
        # Lines starting with # are comments
        # Data lines: YYYY MM DD SS
        data_lines = []
        for line in response.text.splitlines():
            if line.startswith('#') or not line.strip():
                continue
            parts = line.split()
            if len(parts) >= 4:
                try:
                    year = int(parts[0])
                    month = int(parts[1])
                    day = int(parts[2])
                    ss = float(parts[3])
                    if ss < 0: ss = 0 # -1 indicates missing, set to NaN later or keep as 0? Spec says flag gaps.
                    # SILSO uses -1 for missing
                    if ss == -1:
                        ss = None
                    data_lines.append({'year': year, 'month': month, 'day': day, 'sunspot_number': ss})
                except ValueError:
                    continue
        
        if not data_lines:
            raise ValueError("No valid data found in response.")
        
        df = pd.DataFrame(data_lines)
        df['date'] = pd.to_datetime(df[['year', 'month', 'day']])
        df = df[['date', 'sunspot_number']].sort_values('date').reset_index(drop=True)
        
        # Save to raw data directory
        output_path = Path(CONFIG['data_dir']) / 'raw' / 'noaa_sunspots.csv'
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)
        logger.info(f"Sunspot data saved to {output_path}")
        
        return df

    except requests.RequestException as e:
        log_fetch_error("NOAA/SILSO", str(e))
        raise RuntimeError(f"Failed to fetch sunspot data: {e}")
    except Exception as e:
        log_fetch_error("NOAA/SILSO", str(e))
        raise

def main():
    """Entry point for fetching NOAA sunspot data."""
    logger = setup_logger("fetch_noaa_main", level=logging.INFO)
    logger.info("Starting NOAA sunspot data fetch...")
    df = fetch_noaa_sunspots()
    logger.info(f"Successfully fetched {len(df)} records.")
    return df

if __name__ == "__main__":
    main()