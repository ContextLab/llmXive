import os
import sys
import json
import logging
import hashlib
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

import pandas as pd
import requests

from src.config import get_config
from src.lib.utils import setup_logging, load_json, save_csv, save_yaml, ensure_directory, compute_file_checksum
from src.data.provenance import add_provenance_entry, PROVENANCE_FILE_PATH

# Configure logging
logger = logging.getLogger(__name__)

# Constants for Nature's Notebook API
NN_API_BASE = "https://www.usanpn.org/api/v2"
NN_SEARCH_ENDPOINT = f"{NN_API_BASE}/observations"
NN_PARAM_FIELDS = "observation_date,phenophase_name,stage,latitude,longitude,location_name,site_name"

def fetch_nature_notebook_phenology(
    sites: List[Dict[str, Any]],
    start_date: str = "2018-01-01",
    end_date: str = "2023-12-31",
    radius_km: float = 5.0
) -> pd.DataFrame:
    """
    Fetch ground-truth phenology observations from Nature's Notebook API.

    Uses radius search to map observations to the selected sites defined in T011a.
    Iterates through each site, querying the API for observations within the
    specified radius and date range.

    Args:
        sites: List of site dictionaries containing 'latitude', 'longitude', 'site_id'
        start_date: Start date for observation retrieval (YYYY-MM-DD)
        end_date: End date for observation retrieval (YYYY-MM-DD)
        radius_km: Search radius in kilometers around each site

    Returns:
        pd.DataFrame: Combined DataFrame of all observations with site_id appended
    
    Raises:
        RuntimeError: If the API fails to return data for any site (fails loudly)
    """
    config = get_config()
    all_observations = []
    
    # API Key handling (optional but recommended for higher rate limits)
    api_key = config.get("nature_notebook_api_key", None)
    headers = {"Accept": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    logger.info(f"Fetching Nature's Notebook data for {len(sites)} sites...")
    logger.info(f"Date range: {start_date} to {end_date}, Radius: {radius_km}km")

    for site in sites:
        site_id = site.get("site_id")
        lat = site.get("latitude")
        lon = site.get("longitude")

        if lat is None or lon is None:
            logger.warning(f"Skipping site {site_id} due to missing coordinates")
            continue

        # Nature's Notebook API parameters
        params = {
            "latitude": lat,
            "longitude": lon,
            "radius": radius_km * 1000,  # API expects meters
            "start_date": start_date,
            "end_date": end_date,
            "fields": NN_PARAM_FIELDS,
            "limit": 1000,  # Max per page
            "page": 1
        }

        site_observations = []
        total_fetched = 0

        while True:
            try:
                logger.debug(f"Querying NN API for site {site_id} (page {params['page']})")
                response = requests.get(NN_SEARCH_ENDPOINT, headers=headers, params=params, timeout=60)
                
                if response.status_code == 200:
                    data = response.json()
                    results = data.get("results", [])
                    
                    if not results:
                        break
                    
                    # Enrich with site_id
                    for obs in results:
                        obs["site_id"] = site_id
                        obs["source"] = "nature_notebook"
                    site_observations.extend(results)
                    total_fetched += len(results)
                    
                    # Pagination handling
                    if len(results) < params["limit"]:
                        break
                    params["page"] += 1
                    time.sleep(0.5)  # Rate limiting
                else:
                    # Fail loudly: do not silently skip
                    raise RuntimeError(
                        f"Nature's Notebook API error for site {site_id}: "
                        f"HTTP {response.status_code} - {response.text}"
                    )

            except requests.exceptions.RequestException as e:
                raise RuntimeError(
                    f"Failed to fetch Nature's Notebook data for site {site_id}: {e}"
                )

        logger.info(f"Retrieved {total_fetched} observations for site {site_id}")
        all_observations.extend(site_observations)

    if not all_observations:
        # Fail loudly: no data found
        raise RuntimeError(
            "No phenology observations found from Nature's Notebook for any of the selected sites. "
            "Verify site coordinates and date ranges."
        )

    df = pd.DataFrame(all_observations)
    
    # Standardize column names for downstream processing
    # Map API response fields to internal schema
    rename_map = {
        "observation_date": "date",
        "phenophase_name": "phenophase",
        "stage": "stage",
        "location_name": "location_name",
        "site_name": "site_name",
        "latitude": "obs_latitude",
        "longitude": "obs_longitude"
    }
    
    # Only rename if columns exist
    existing_renames = {k: v for k, v in rename_map.items() if k in df.columns}
    df = df.rename(columns=existing_renames)
    
    # Ensure date column is datetime
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
    
    # Sort by site_id and date
    df = df.sort_values(by=["site_id", "date"]).reset_index(drop=True)

    return df

def save_phenology_data(df: pd.DataFrame, output_path: str) -> str:
    """
    Save phenology DataFrame to CSV and update provenance.
    
    Args:
        df: DataFrame containing phenology observations
        output_path: Path to save the CSV file
        
    Returns:
        str: Checksum of the saved file
    """
    ensure_directory(Path(output_path))
    
    # Save to CSV
    save_csv(df, output_path)
    checksum = compute_file_checksum(output_path)
    
    # Update provenance
    add_provenance_entry(
        file_path=output_path,
        source="Nature's Notebook API",
        params={
            "date_range": f"{df['date'].min()} to {df['date'].max()}",
            "total_observations": len(df),
            "unique_sites": df["site_id"].nunique()
        },
        checksum=checksum
    )
    
    logger.info(f"Saved phenology data to {output_path} (checksum: {checksum})")
    return checksum

def run_nature_notebook_ingestion() -> str:
    """
    Main entry point for fetching and saving Nature's Notebook phenology data.
    
    Returns:
        str: Path to the saved CSV file
    """
    config = get_config()
    
    # Load selected sites from the intermediate file generated by T011a/T011
    # Assuming sites are saved in data/processed/selected_sites.json by previous tasks
    sites_path = config.get("paths", {}).get("selected_sites", "data/processed/selected_sites.json")
    
    if not os.path.exists(sites_path):
        raise FileNotFoundError(
            f"Selected sites file not found at {sites_path}. "
            "Run T011a and T011 first to generate this file."
        )
    
    sites = load_json(sites_path)
    if not isinstance(sites, list):
        raise ValueError(f"Expected list of sites in {sites_path}, got {type(sites)}")
    
    # Fetch data
    df = fetch_nature_notebook_phenology(
        sites=sites,
        start_date=config.get("data", {}).get("start_year", 2018),
        end_date=config.get("data", {}).get("end_year", 2023),
        radius_km=config.get("data", {}).get("phenology_radius_km", 5.0)
    )
    
    # Save output
    output_path = config.get("paths", {}).get("phenology_observations", "data/processed/phenology_observations.csv")
    save_phenology_data(df, output_path)
    
    return output_path

def main():
    """CLI entry point."""
    setup_logging()
    try:
        output_path = run_nature_notebook_ingestion()
        logger.info(f"Success. Phenology data saved to: {output_path}")
    except Exception as e:
        logger.error(f"Failed to ingest phenology data: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
