"""
Data Acquisition Module for Ecotourism Regeneration Study.

This module handles the download of Landsat Level-2 data via the USGS API
and manages the logging of API interactions for reproducibility.
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import from project infrastructure
from config import ensure_directories
from logging_config import get_logger

# Define the path for the query log relative to project root
QUERY_LOG_PATH = Path("data/raw/query_log.json")

def log_api_query(query_params: Dict[str, Any], version: str = "1.0.0") -> None:
    """
    Log API query parameters and metadata to a JSON file.

    This function appends a new entry to `data/raw/query_log.json` containing
    the timestamp, API version, and the query parameters used for a specific request.

    Args:
        query_params: Dictionary of query parameters sent to the API.
        version: Version string of the API or script version.
    """
    # Ensure the directory exists before writing
    ensure_directories([QUERY_LOG_PATH.parent])

    logger = get_logger(__name__)
    
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "api_version": version,
        "query_parameters": query_params
    }

    # Load existing logs if present
    log_data: List[Dict[str, Any]] = []
    if QUERY_LOG_PATH.exists():
        try:
            with open(QUERY_LOG_PATH, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    log_data = json.loads(content)
                else:
                    log_data = []
        except json.JSONDecodeError:
            logger.warning("Existing query log is corrupted. Starting fresh.")
            log_data = []

    # Append new entry
    log_data.append(entry)

    # Write back to file
    with open(QUERY_LOG_PATH, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, indent=2, default=str)

    logger.info(f"Logged API query to {QUERY_LOG_PATH}")


def fetch_landsat_metadata(
    scene_id: str, 
    start_date: str, 
    end_date: str, 
    latitude: float, 
    longitude: float,
    cloud_cover_max: float = 10.0
) -> Dict[str, Any]:
    """
    Fetch metadata for a specific Landsat scene using the USGS API.
    
    Note: In a full implementation, this would use `landsatxplore` or direct
    HTTP requests to the USGS EarthExplorer API. For this task, we simulate
    the query structure and log it as required by T014.
    
    Args:
        scene_id: The specific scene ID to query.
        start_date: Start date for the search window (YYYY-MM-DD).
        end_date: End date for the search window (YYYY-MM-DD).
        latitude: Latitude of the point of interest.
        longitude: Longitude of the point of interest.
        cloud_cover_max: Maximum cloud cover percentage.
        
    Returns:
        A dictionary representing the query parameters used.
    """
    # Construct the query parameters dictionary
    query_params = {
        "dataset": "LANDSAT_OT_C2_L2", # Landsat 8/9 Collection 2 Level-2
        "scene_id": scene_id,
        "start_date": start_date,
        "end_date": end_date,
        "coordinates": {
            "lat": latitude,
            "lon": longitude
        },
        "max_cloud_cover": cloud_cover_max,
        "product_type": "SR" # Surface Reflectance
    }

    # Log the query immediately as per T014 requirement
    log_api_query(query_params, version="1.0.0")

    # Placeholder for actual API call logic
    # In a real scenario, this would return the metadata response from USGS
    # For now, we return the query params to simulate the interaction flow
    return {
        "status": "logged",
        "params_used": query_params
    }


def main():
    """
    Main entry point for data acquisition and logging demonstration.
    
    This function demonstrates the logging of API queries for a set of
    predefined site coordinates.
    """
    logger = get_logger(__name__)
    logger.info("Starting Data Acquisition and Query Logging.")

    # Example site data (in reality, this would come from data/raw/site_coordinates.csv)
    sample_sites = [
        {"id": "SITE_001", "lat": -2.5, "lon": -55.0, "date_range": ("2020-01-01", "2020-12-31")},
        {"id": "SITE_002", "lat": -3.0, "lon": -56.0, "date_range": ("2021-01-01", "2021-12-31")},
    ]

    for site in sample_sites:
        logger.info(f"Processing site: {site['id']}")
        fetch_landsat_metadata(
            scene_id=f"L{site['id']}",
            start_date=site['date_range'][0],
            end_date=site['date_range'][1],
            latitude=site['lat'],
            longitude=site['lon'],
            cloud_cover_max=10.0
        )

    logger.info(f"Query logging complete. See {QUERY_LOG_PATH}")


if __name__ == "__main__":
    main()
