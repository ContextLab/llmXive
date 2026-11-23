import os
import sys
import logging
import json
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any, List
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import time

# --- Configuration & Constants ---
WORLD_BANK_API_URL = "https://api.worldbank.org/v2/country/all/indicator"
INDICATORS = [
    "SP.POP.DPGE",  # Population by age and sex (Annual %) - Proxy for age distribution
    "SP.DYN.LE00.IN" # Life expectancy at birth, total (years) - Proxy for general health/age
]
INDICATOR_MAP = {
    "SP.POP.DPGE": "population_age_sex_pct",
    "SP.DYN.LE00.IN": "life_expectancy"
}

# --- Logging Setup ---
def setup_custom_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

# --- Directory Management ---
def ensure_directories(base_path: Path) -> None:
    processed_dir = base_path / "data" / "processed"
    logs_dir = base_path / "results" / "logs"
    processed_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)

# --- Geocoding Helper ---
def get_country_code_from_coords(lat: float, lon: float, geolocator: Nominatim) -> Optional[str]:
    """
    Reverse geocode lat/lon to get ISO-3 country code.
    Returns None if geocoding fails or times out.
    """
    if pd.isna(lat) or pd.isna(lon):
        return None
    try:
        location = geolocator.reverse(f"{lat}, {lon}", timeout=10)
        if location and location.raw:
            address = location.raw.get('address', {})
            country_code = address.get('country_code') # Usually 2-letter (e.g., 'us')
            if country_code:
                # Convert to 3-letter ISO (e.g., 'usa') if needed, but World Bank often accepts 2-letter or specific codes.
                # World Bank API usually accepts 2-letter codes (ISO 3166-1 alpha-2) or 'all'.
                # We will return the 2-letter code as it is standard for World Bank.
                return country_code.upper()
    except (GeocoderTimedOut, GeocoderServiceError) as e:
        logging.warning(f"Geocoding failed for ({lat}, {lon}): {e}")
    except Exception as e:
        logging.warning(f"Unexpected error geocoding ({lat}, {lon}): {e}")
    return None

# --- World Bank Data Fetching ---
def fetch_world_bank_indicator(indicator_id: str, country_codes: List[str]) -> pd.DataFrame:
    """
    Fetches data for a specific indicator from World Bank API.
    Returns a DataFrame with columns: country_code, year, value.
    """
    import requests
    data_list = []
    # World Bank API returns JSON. We need to handle pagination if necessary, but for these indicators it's usually one page.
    # We will fetch the most recent year available (or a range if needed).
    # Let's fetch the latest 5 years to be safe, or just the latest.
    # API format: /indicator/{id}?format=json&date={start}:{end}
    # We'll try to get the latest data.
    
    url = f"{WORLD_BANK_API_URL}/{indicator_id}"
    params = {
        "format": "json",
        "date": "2014:2018", # Match our study period
        "per_page": 3000     # Max per page
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        json_data = response.json()
        
        if isinstance(json_data, list) and len(json_data) > 1:
            records = json_data[1] # First element is metadata, second is data
            for record in records:
                country_id = record.get('country', {}).get('id')
                value = record.get('value')
                year = record.get('date')
                if country_id and value is not None and str(year) in ["2014", "2015", "2016", "2017", "2018"]:
                    # Filter for our country codes if provided (optional optimization)
                    if not country_codes or country_id.upper() in [c.upper() for c in country_codes]:
                        data_list.append({
                            "country_code": country_id,
                            "year": year,
                            "value": value
                        })
    except requests.RequestException as e:
        logging.error(f"Failed to fetch World Bank data for {indicator_id}: {e}")
        return pd.DataFrame(columns=["country_code", "year", "value"])
    
    return pd.DataFrame(data_list)

def fetch_demographic_data(unique_countries: List[str]) -> pd.DataFrame:
    """
    Fetches demographic data for a list of unique country codes.
    Returns a merged DataFrame with indicators.
    """
    all_data = []
    for indicator_id in INDICATORS:
        logging.info(f"Fetching World Bank data for indicator: {indicator_id}")
        df = fetch_world_bank_indicator(indicator_id, unique_countries)
        if not df.empty:
            df['indicator'] = indicator_id
            all_data.append(df)
        
        # Be nice to the API
        time.sleep(1)

    if not all_data:
        logging.warning("No demographic data fetched from World Bank.")
        return pd.DataFrame()

    combined_df = pd.concat(all_data, ignore_index=True)
    
    # Pivot to wide format: country_code, year, indicator -> value
    # We want: country_code, year, population_age_sex_pct, life_expectancy
    pivot_df = combined_df.pivot_table(
        index=['country_code', 'year'],
        columns='indicator',
        values='value',
        aggfunc='first' # In case of duplicates, take first
    ).reset_index()
    
    # Rename columns based on map
    pivot_df.rename(columns=INDICATOR_MAP, inplace=True)
    
    return pivot_df

# --- Gap Logging ---
def log_gap(missing_countries: List[str], log_path: Path) -> None:
    """Logs countries for which covariates could not be fetched or derived."""
    if missing_countries:
        log_entry = {
            "status": "partial_missing",
            "missing_countries": list(set(missing_countries)),
            "count": len(set(missing_countries))
        }
        with open(log_path, 'w') as f:
            json.dump(log_entry, f, indent=2)
        logging.warning(f"Failed to fetch covariates for {len(missing_countries)} unique countries.")
    else:
        log_entry = {"status": "complete"}
        with open(log_path, 'w') as f:
            json.dump(log_entry, f, indent=2)

# --- Main Logic ---
def merge_demographics_to_data(moral_data: pd.DataFrame, demo_data: pd.DataFrame) -> pd.DataFrame:
    """
    Merges demographic data into the moral machine dataset.
    Assumes moral_data has 'country' (ISO-3 or name) or lat/lon.
    We will use 'country' if available, else derive from lat/lon (handled before this call).
    Here we assume 'country' in moral_data is the ISO-2 code (from geocoding) or needs mapping.
    World Bank uses ISO-3 usually, but API often accepts ISO-2.
    Let's assume the 'country' column in moral_data is the ISO-2 code derived from geocoding.
    """
    if demo_data.empty:
        logging.warning("Demo data is empty, returning original data with NaN covariates.")
        moral_data['population_age_sex_pct'] = pd.NA
        moral_data['life_expectancy'] = pd.NA
        return moral_data

    # Ensure country column in moral_data is string and upper case for matching
    if 'country' not in moral_data.columns:
        logging.error("Moral data missing 'country' column. Cannot merge demographics.")
        return moral_data

    moral_data['country'] = moral_data['country'].astype(str).str.upper()
    demo_data['country_code'] = demo_data['country_code'].astype(str).str.upper()

    # We need to match by country and ideally year.
    # Since moral data might not have exact year match for every row, we can:
    # 1. Merge on country only (average across years)
    # 2. Merge on country and year (if year is available in moral data)
    
    # Check if 'year' exists in moral data
    if 'year' in moral_data.columns:
        moral_data['year'] = moral_data['year'].astype(str)
        merged = pd.merge(
            moral_data,
            demo_data,
            left_on=['country', 'year'],
            right_on=['country_code', 'year'],
            how='left'
        )
        merged.drop(columns=['country_code'], inplace=True, errors='ignore')
    else:
        # No year in moral data, merge on country only (taking mean of available years)
        demo_mean = demo_data.groupby('country_code').mean().reset_index()
        merged = pd.merge(
            moral_data,
            demo_mean,
            left_on='country',
            right_on='country_code',
            how='left'
        )
        merged.drop(columns=['country_code'], inplace=True, errors='ignore')

    return merged

def main():
    base_path = Path(os.getcwd())
    ensure_directories(base_path)
    logger = setup_custom_logger("derive_demographics")
    
    input_path = base_path / "data" / "processed" / "merged_dataset.parquet"
    output_path = base_path / "data" / "processed" / "covariates.csv"
    log_path = base_path / "results" / "logs" / "covariate_status.json"

    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)

    try:
        logger.info(f"Loading data from {input_path}")
        df = pd.read_parquet(input_path)

        # Step 1: Ensure 'country' column exists and is ISO-2
        if 'country' not in df.columns:
            logger.warning("No 'country' column found. Attempting to derive from lat/lon.")
            geolocator = Nominatim(user_agent="llmXive_moral_temp_study")
            df['country'] = df.apply(
                lambda row: get_country_code_from_coords(row['latitude'], row['longitude'], geolocator),
                axis=1
            )
            # Save the geocoded country if it was missing
            df.to_parquet(input_path, index=False)

        # Step 2: Identify unique countries
        unique_countries = df['country'].dropna().unique().tolist()
        logger.info(f"Found {len(unique_countries)} unique countries.")

        # Step 3: Fetch World Bank Data
        demo_df = fetch_demographic_data(unique_countries)

        # Step 4: Merge
        final_df = merge_demographics_to_data(df, demo_df)

        # Step 5: Extract covariates only (for the specific task output)
        covariate_cols = ['country', 'population_age_sex_pct', 'life_expectancy']
        # Filter to columns that exist
        available_cols = [c for c in covariate_cols if c in final_df.columns]
        covariates_df = final_df[available_cols].copy()
        
        # Drop duplicates to keep one row per country (as per task "save to covariates.csv")
        # Or keep all rows? Task says "save to data/processed/covariates.csv".
        # Usually covariates are joined back. Let's save the unique mapping for reference.
        unique_covariates = covariates_df.drop_duplicates(subset=['country'])
        
        unique_covariates.to_csv(output_path, index=False)
        logger.info(f"Covariates saved to {output_path}")

        # Step 6: Log status
        missing = [c for c in unique_countries if c not in unique_covariates['country'].values]
        log_gap(missing, log_path)

    except Exception as e:
        logger.error(f"Error processing demographics: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
