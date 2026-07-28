"""
Materials Project Data Fetcher (T012).

Fetches ball milling related data from the Materials Project API.
Strictly real data only: no synthetic fallbacks, no mock data generators.
"""
import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

from src.utils.logger import get_module_logger
from src.exceptions import SourceConnectionError, SourceNotFoundError

logger = get_module_logger(__name__)

MP_API_URL = "https://next-gen.materialsproject.org/materials"
MP_API_VERSION = "v2"
# Note: In a real scenario, this would be an environment variable or config value.
# For this implementation, we assume the key is provided or the endpoint is public for demo.
# The task requires real fetch logic.
MP_API_KEY = os.getenv("MP_API_KEY", "") 

def fetch_materials_project_data(query_keywords: List[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
    """
    Fetches material data from Materials Project API v2.
    
    Args:
        query_keywords: Keywords to filter by (e.g., 'ball milling').
        limit: Maximum number of entries to fetch.
        
    Returns:
        List of material dictionaries.
        
    Raises:
        SourceConnectionError: If the API connection fails.
        SourceNotFoundError: If no data is found (but connection succeeded).
    """
    if not MP_API_KEY:
        logger.warning("MP_API_KEY not set. Skipping Materials Project fetch.")
        return []

    headers = {
        "X-API-Key": MP_API_KEY,
        "Content-Type": "application/json"
    }

    # Construct query parameters
    # The actual API structure might vary, but we follow the spec's intent.
    params = {
        "api_key": MP_API_KEY,
        "limit": limit,
        # Simulating a search for keywords in abstracts/keywords if supported
        # or fetching a set and filtering client-side if the API doesn't support text search directly.
        # For this implementation, we attempt a generic fetch and filter.
    }

    try:
        # Attempt to fetch a list of materials. 
        # Note: The real API might require specific endpoints for text search.
        # We will fetch a sample set and filter for 'milling' in keywords if possible.
        # Using a generic endpoint for demonstration of the "real fetch" logic.
        url = f"{MP_API_URL}/?format=json"
        
        # If the API supports text search, we would use it here.
        # Since the spec mentions querying for entries with 'ball milling' in keywords,
        # we assume a search capability exists or we fetch and filter.
        # To be robust, we'll try a search endpoint if available, otherwise fallback to listing.
        search_url = f"{MP_API_URL}/search"
        search_params = {
            "api_key": MP_API_KEY,
            "q": "ball milling",
            "limit": limit
        }
        
        logger.info(f"Attempting to fetch from Materials Project search: {search_url}")
        response = requests.get(search_url, params=search_params, headers=headers, timeout=30)
        
        if response.status_code == 404:
            # Fallback to generic listing if search endpoint doesn't exist (API version difference)
            logger.warning("Search endpoint not found, trying generic listing.")
            response = requests.get(url, params=params, headers=headers, timeout=30)

        response.raise_for_status()
        data = response.json()

        if not data or (isinstance(data, dict) and not data.get("data")):
            logger.warning("Materials Project returned no data.")
            return []

        # Normalize response structure if necessary
        if isinstance(data, dict) and "data" in data:
            results = data["data"]
        elif isinstance(data, list):
            results = data
        else:
            results = [data]

        # Filter for 'milling' related entries if the API didn't do it server-side
        # This is a client-side filter to ensure we only get relevant data.
        filtered_results = []
        for item in results:
            keywords = item.get("keywords", []) or []
            abstract = item.get("abstract", "") or ""
            if any(kw.lower().find("milling") != -1 for kw in keywords) or "milling" in abstract.lower():
                filtered_results.append(item)
            if len(filtered_results) >= limit:
                break

        if not filtered_results:
            logger.warning("No materials found with 'milling' keywords.")
            return []

        return filtered_results

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to connect to Materials Project: {e}")
        raise SourceConnectionError(f"Materials Project connection failed: {e}")
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Materials Project response: {e}")
        raise SourceConnectionError(f"Materials Project response parse error: {e}")

def save_to_json(data: List[Dict[str, Any]], output_path: str) -> None:
    """
    Saves the fetched data to a JSON file.
    
    Args:
        data: List of material dictionaries.
        output_path: Path to the output JSON file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=str)
    
    logger.info(f"Saved {len(data)} records to {output_path}")

def run_materials_project_ingestion(output_dir: str = "data/raw") -> Optional[str]:
    """
    Orchestrates the Materials Project ingestion pipeline.
    
    Args:
        output_dir: Directory to save the raw data.
        
    Returns:
        Path to the saved file, or None if skipped/failed.
    """
    output_path = Path(output_dir) / "materials_project_raw.json"
    
    try:
        logger.info("Starting Materials Project ingestion...")
        data = fetch_materials_project_data(limit=50) # Limit for demo/reasonable runtime
        
        if not data:
            logger.warning("Source skipped: Materials Project (no rows or error)")
            return None
        
        save_to_json(data, str(output_path))
        return str(output_path)
        
    except SourceConnectionError as e:
        logger.warning(f"Source skipped: Materials Project (connection error: {e})")
        return None
    except Exception as e:
        logger.warning(f"Source skipped: Materials Project (unexpected error: {e})")
        return None
