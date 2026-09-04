import os
import sys
import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import requests

from utils.config import get_env_var
from utils.io import setup_logging, fail_loud_loader

logger = logging.getLogger(__name__)

# Constants
MP_API_URL = "https://next-gen.materialsproject.org/materials/v2/"
AFLOW_URL = "http://aflow.org/rest/"
ZENODO_API_URL = "https://zenodo.org/api/records"

def fetch_materials_project_data(api_key: str) -> Optional[Dict[str, Any]]:
    """
    Fetch metallic glass data from Materials Project API.
    Filters for amorphous structures if supported by the endpoint.
    """
    headers = {"Authorization": f"Bearer {api_key}"}
    params = {
        "elements": "Zr,Cu,Al,Pd,Fe,Ni", # Common MG elements
        "include": "properties",
        "amorphous": "true"
    }

    try:
        # Note: The exact query parameters depend on the specific MP API version
        # This is a robust attempt to fetch the data
        response = requests.get(MP_API_URL, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        if data and "data" in data:
            logger.info(f"Retrieved {len(data['data'])} entries from Materials Project.")
            return data
        return None
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 403:
            logger.warning("Materials Project API returned 403 (Unauthorized).")
        elif e.response.status_code == 404:
            logger.warning("Materials Project endpoint not found (404).")
        else:
            logger.error(f"Materials Project API error: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching from Materials Project: {e}")
        return None

def fetch_aflow_data(api_key: str) -> Optional[Dict[str, Any]]:
    """
    Fetch data from AFLOWlib API.
    """
    headers = {"Authorization": f"Bearer {api_key}"}
    params = {
        "structure_type": "amorphous",
        "properties": "composition,cte"
    }

    try:
        response = requests.get(AFLOW_URL, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        if data:
            logger.info(f"Retrieved data from AFLOWlib.")
            return data
        return None
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 403:
            logger.warning("AFLOWlib API returned 403 (Unauthorized).")
        else:
            logger.error(f"AFLOWlib API error: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching from AFLOWlib: {e}")
        return None

def fetch_zenodo_fallback(zenodo_id: str) -> Optional[Dict[str, Any]]:
    """
    Fallback to Zenodo dataset if APIs fail or return insufficient data.
    Uses the provided ZENODO_ID to fetch the dataset metadata and files.
    """
    url = f"{ZENODO_API_URL}/{zenodo_id}"
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        if data:
            logger.info(f"Retrieved fallback data from Zenodo ID: {zenodo_id}")
            return data
        return None
    except Exception as e:
        logger.error(f"Error fetching from Zenodo: {e}")
        return None

@fail_loud_loader
def fetch_data() -> Tuple[Optional[Dict[str, Any]], str]:
    """
    Orchestrates data fetching from MP, AFLOW, and Zenodo.
    Returns the data source and the fetched data.
    Raises DataFetchError if no valid data is found.
    """
    mp_key = get_env_var("MP_API_KEY")
    aflow_key = get_env_var("AFLOWlib_API_KEY")
    zenodo_id = get_env_var("ZENODO_ID", default="1234567")

    data = None
    source = "none"

    # Try Materials Project
    if mp_key:
        data = fetch_materials_project_data(mp_key)
        if data:
            source = "materials_project"
            return data, source

    # Try AFLOWlib
    if aflow_key:
        data = fetch_aflow_data(aflow_key)
        if data:
            source = "aflowlib"
            return data, source

    # Fallback to Zenodo
    logger.warning("APIs failed or returned insufficient data. Triggering Zenodo fallback.")
    data = fetch_zenodo_fallback(zenodo_id)
    if data:
        source = "zenodo"
        return data, source

    # If we reach here, all sources failed
    raise RuntimeError("No valid metallic glass entries found in API or Zenodo.")

def main():
    """
    Entry point for the ingestion script.
    """
    setup_logging()
    try:
        data, source = fetch_data()
        logger.info(f"Successfully fetched data from {source}.")
        # In a real pipeline, this would save to data/raw
        # For this task, we just confirm the fetch logic works
        print(f"Data fetched from {source}: {len(data) if isinstance(data, dict) else 'unknown'}")
    except Exception as e:
        logger.critical(f"Data ingestion failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
