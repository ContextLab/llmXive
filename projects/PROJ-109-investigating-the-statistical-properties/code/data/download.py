import os
import time
import requests
import h5py
import numpy as np
from pathlib import Path
import logging

from utils.logging import get_logger
from data.synthetic_generator import generate_synthetic_halos
from config import (
    ILLUSTRIS_API_BASE,
    MILLENNIUM_API_BASE,
    ILLUSTRIS_TOKEN,
    SYNTHETIC_OUTPUT_PATH,
    LOG_LEVEL,
    LOG_FORMAT,
    LOGS_DIR
)

logger = get_logger(__name__)

def check_api_status(base_url: str, token: str = None) -> bool:
    """
    Check if the API is accessible.
    Returns True if accessible (200 OK), False otherwise.
    """
    try:
        headers = {"Authorization": f"Token {token}"} if token else {}
        # Attempt a lightweight HEAD or GET to the base or a known endpoint
        # Using the base URL as a probe; adjust if a specific health endpoint exists
        response = requests.get(base_url, headers=headers, timeout=10)
        if response.status_code == 200:
            logger.info(f"API accessible: {base_url}")
            return True
        else:
            logger.warning(f"API returned status {response.status_code} for {base_url}")
            return False
    except requests.exceptions.RequestException as e:
        logger.warning(f"API check failed for {base_url}: {e}")
        return False

def fetch_illustris_halos(output_path: Path) -> bool:
    """
    Fetch IllustrisTNG TNG100-1 catalog.
    Returns True if successful, False if data gap detected.
    """
    logger.info(f"Attempting to fetch IllustrisTNG data to {output_path}")
    try:
        # Construct the URL for the halo catalog (example endpoint structure)
        # In a real scenario, this would be the specific endpoint for the SubFind catalog
        url = f"{ILLUSTRIS_API_BASE}/halos/"
        params = {"key": "Subfind"} # Example parameter
        headers = {"Authorization": f"Token {ILLUSTRIS_TOKEN}"}

        response = requests.get(url, headers=headers, params=params, timeout=60)

        if response.status_code == 200:
            # Save the raw JSON or HDF5 content
            with open(output_path, 'wb') as f:
                f.write(response.content)
            logger.info("IllustrisTNG data fetched successfully.")
            return True
        elif response.status_code == 403:
            logger.error("Access forbidden (403). API token might be invalid or expired.")
            return False
        else:
            logger.error(f"Failed to fetch IllustrisTNG data. Status: {response.status_code}")
            return False

    except requests.exceptions.Timeout:
        logger.error("Request to IllustrisTNG API timed out.")
        return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
        return False

def fetch_millennium_halos(output_path: Path) -> bool:
    """
    Fetch Millennium Simulation catalog.
    Returns True if successful, False if data gap detected.
    """
    logger.info(f"Attempting to fetch Millennium data to {output_path}")
    try:
        # Millennium data often resides on specific servers or requires FTP/HTTP
        # Using a placeholder URL structure as per project config
        url = f"{MILLENNIUM_API_BASE}/catalogs/halos.hdf5"
        
        response = requests.get(url, timeout=60)

        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                f.write(response.content)
            logger.info("Millennium data fetched successfully.")
            return True
        elif response.status_code == 403:
            logger.error("Access forbidden (403).")
            return False
        else:
            logger.error(f"Failed to fetch Millennium data. Status: {response.status_code}")
            return False

    except requests.exceptions.Timeout:
        logger.error("Request to Millennium API timed out.")
        return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
        return False

def run_data_pipeline():
    """
    Orchestrates the data acquisition pipeline.
    Attempts real download -> If HTTP 403/Timeout/404, logs 'DATA_GAP' -> Triggers synthetic fallback.
    """
    logger.info("Starting data acquisition pipeline.")
    
    illustris_path = Path("data/raw/illustris_halos.h5")
    millennium_path = Path("data/raw/millennium_halos.h5")
    
    success_illustris = False
    success_millennium = False

    # Attempt IllustrisTNG
    if not check_api_status(ILLUSTRIS_API_BASE, ILLUSTRIS_TOKEN):
        logger.warning("IllustrisTNG API check failed initially.")
    
    success_illustris = fetch_illustris_halos(illustris_path)

    if not success_illustris:
        # Log the specific data gap message as required by T016
        logger.info("DATA_GAP: Real data unavailable, switching to synthetic")
        generate_synthetic_halos(illustris_path)
        logger.info("Synthetic IllustrisTNG data generated.")

    # Attempt Millennium
    if not check_api_status(MILLENNIUM_API_BASE):
        logger.warning("Millennium API check failed initially.")

    success_millennium = fetch_millennium_halos(millennium_path)

    if not success_millennium:
        # Log the specific data gap message as required by T016
        logger.info("DATA_GAP: Real data unavailable, switching to synthetic")
        generate_synthetic_halos(millennium_path)
        logger.info("Synthetic Millennium data generated.")

    logger.info("Data acquisition pipeline completed.")
    return illustris_path, millennium_path

if __name__ == "__main__":
    run_data_pipeline()