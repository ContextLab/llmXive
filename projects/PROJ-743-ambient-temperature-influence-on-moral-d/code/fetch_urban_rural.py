import os
import sys
import logging
import json
import argparse
from pathlib import Path
from typing import Optional, List, Dict, Any

import pandas as pd
import numpy as np

# Attempt to import geopy; if missing, the script will fail loudly as per constraints
try:
    from geopy.geocoders import Nominatim
    from geopy.exc import GeocoderTimedOut, GeocoderServiceError
    GEOPY_AVAILABLE = True
except ImportError:
    GEOPY_AVAILABLE = False
    Nominatim = None
    GeocoderTimedOut = None
    GeocoderServiceError = None

# Import project config for paths
from config import get_path_env_override
from setup_logging import setup_logging, get_data_quality_logger

def ensure_directories(output_path: Path) -> None:
    """Ensure the output directory exists."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

def classify_coordinate(
    lat: float,
    lon: float,
    geolocator: Optional[Nominatim]
) -> Optional[str]:
    """
    Classify a single coordinate as 'urban' or 'rural' using reverse geocoding.
    
    Returns:
        'urban', 'rural', or None if classification failed.
    """
    if geolocator is None:
        return None

    try:
        location = geolocator.reverse(f"{lat}, {lon}", timeout=10, language='en')
        if location is None:
            return None
        
        raw_address = location.raw.get('address', {})
        
        # Heuristic: Check for 'city', 'town', 'village', 'county' in address hierarchy
        # or check if the place_type suggests an urban center.
        # Nominatim often returns 'city', 'town', 'village', 'hamlet' in the 'place' key.
        
        place = raw_address.get('place')
        city = raw_address.get('city')
        town = raw_address.get('town')
        village = raw_address.get('village')
        hamlet = raw_address.get('hamlet')
        suburb = raw_address.get('suburb')
        neighbourhood = raw_address.get('neighbourhood')
        county = raw_address.get('county')
        state = raw_address.get('state')
        
        # Prioritize urban indicators
        urban_indicators = [city, town, suburb, neighbourhood, place]
        if any(indicator and str(indicator).lower() not in ['', 'none'] for indicator in urban_indicators):
            # Further refine: if it's a hamlet or village, it might be rural depending on context,
            # but for this proxy, we often treat populated places as 'urban' relative to open country.
            # However, strict 'rural' usually means 'hamlet' or just 'county' without specific town.
            
            # Simple heuristic: if it has a specific settlement name (city/town/village/suburb), call it urban.
            # If it only has county/state/road, call it rural.
            if any(indicator for indicator in [city, town, suburb, neighbourhood]):
                return 'urban'
            if place:
                p_lower = str(place).lower()
                if p_lower in ['village', 'hamlet', 'town', 'city']:
                    return 'urban'
                # If it's just a region name, assume rural for safety
                return 'rural'
            
            return 'urban' # Default to urban if we found a place name but it's ambiguous
        
        # Check for rural indicators
        if hamlet:
            return 'rural'
        if village:
            # Villages can be considered rural in this context if no 'town' or 'city'
            return 'rural'
        
        # If we have a county but no specific town, it's likely rural
        if county and not any([city, town, village, hamlet]):
            return 'rural'
        
        # Default fallback: if we got an address but can't classify, assume rural
        # to avoid false positives in open areas.
        return 'rural'

    except (GeocoderTimedOut, GeocoderServiceError, Exception) as e:
        logging.warning(f"Geocoding failed for ({lat}, {lon}): {e}")
        return None

def fetch_urban_rural_data(
    input_path: Path,
    output_path: Path,
    log_path: Path
) -> None:
    """
    Main logic to fetch urban/rural proxy for coordinates in the merged dataset.
    """
    logger = get_data_quality_logger()
    logger.info(f"Starting urban/rural proxy fetch for {input_path}")

    if not GEOPY_AVAILABLE:
        logger.error("geopy is not installed. Cannot fetch urban/rural proxy.")
        # Handle failure by creating empty/NaN file and logging
        ensure_directories(output_path)
        # Create a dummy CSV with NaNs to allow pipeline to continue
        df_nan = pd.DataFrame({'participant_id': [], 'urban_rural': []})
        df_nan.to_csv(output_path, index=False)
        
        status_log = {
            "status": "failed",
            "reason": "geopy module not found",
            "timestamp": str(pd.Timestamp.now())
        }
        with open(log_path, 'w') as f:
            json.dump(status_log, f, indent=2)
        return

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    try:
        df = pd.read_parquet(input_path)
    except Exception as e:
        # Fallback to CSV if parquet fails, though spec says parquet
        try:
            df = pd.read_csv(input_path)
        except Exception as e2:
            raise RuntimeError(f"Could not load input file as parquet or csv: {e2}")

    required_cols = ['latitude', 'longitude']
    if not all(col in df.columns for col in required_cols):
        # Try to find alternate column names if standard ones are missing
        lat_col = 'latitude' if 'latitude' in df.columns else (
            'lat' if 'lat' in df.columns else None
        )
        lon_col = 'longitude' if 'longitude' in df.columns else (
            'lon' if 'lon' in df.columns else None
        )
        
        if lat_col and lon_col:
            df['latitude'] = df[lat_col]
            df['longitude'] = df[lon_col]
        else:
            raise ValueError("Could not find latitude/longitude columns in input data.")

    # Initialize geolocator
    geolocator = Nominatim(user_agent="llmXive_moral_temp_project")

    # Process coordinates
    # Note: This is a serial operation to respect API rate limits.
    # In a production environment, a batch API or caching layer would be used.
    urban_rural_list = []
    failed_count = 0
    total_count = len(df)

    logger.info(f"Processing {total_count} coordinates...")

    for idx, row in df.iterrows():
        lat = row['latitude']
        lon = row['longitude']

        if pd.isna(lat) or pd.isna(lon):
            urban_rural_list.append(None)
            failed_count += 1
            continue

        classification = classify_coordinate(lat, lon, geolocator)
        urban_rural_list.append(classification)

        if classification is None:
            failed_count += 1

        if (idx + 1) % 1000 == 0:
            logger.info(f"Processed {idx + 1}/{total_count} rows")

    df['urban_rural'] = urban_rural_list

    # Log success/failure status
    success_rate = 1.0 - (failed_count / total_count) if total_count > 0 else 0.0
    status = "success" if success_rate > 0.0 else "failed"
    status_log = {
        "status": status,
        "total_processed": total_count,
        "successful_classifications": total_count - failed_count,
        "failed_classifications": failed_count,
        "success_rate": success_rate,
        "timestamp": str(pd.Timestamp.now())
    }

    # Save the proxy data
    ensure_directories(output_path)
    df[['participant_id', 'urban_rural']].to_csv(output_path, index=False)

    # Save status log
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, 'w') as f:
        json.dump(status_log, f, indent=2)

    logger.info(f"Urban/Rural proxy saved to {output_path}")
    logger.info(f"Classification success rate: {success_rate:.2%}")

    if status == "failed":
        logger.warning("Urban/Rural proxy fetch failed completely. Pipeline will proceed with NaNs.")

def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch Urban/Rural proxy for coordinates")
    parser.add_argument(
        "--input",
        type=str,
        default="data/processed/merged_dataset.parquet",
        help="Path to the merged dataset (parquet or csv)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/processed/urban_rural_proxy.csv",
        help="Path to save the urban/rural proxy CSV"
    )
    parser.add_argument(
        "--log",
        type=str,
        default="results/logs/covariate_status.json",
        help="Path to save the status log"
    )
    args = parser.parse_args()

    setup_logging()
    input_path = Path(args.input)
    output_path = Path(args.output)
    log_path = Path(args.log)

    try:
        fetch_urban_rural_data(input_path, output_path, log_path)
    except Exception as e:
        logging.critical(f"Fatal error in fetch_urban_rural: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
