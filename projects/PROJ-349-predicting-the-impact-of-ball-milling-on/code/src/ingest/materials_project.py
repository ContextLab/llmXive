import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
import requests

from src.utils.logger import get_module_logger

logger = get_module_logger(__name__)

MP_API_URL = "https://next-gen.materialsproject.org/materials"
MP_SEARCH_URL = "https://next-gen.materialsproject.org/api/v2/doc/search"

def fetch_materials_project_data(api_key: Optional[str] = None, query_terms: List[str] = None) -> List[Dict[str, Any]]:
    """
    Fetch ball milling data from Materials Project API.
    
    Note: The Materials Project API does not directly provide 'ball milling' 
    specific experimental parameters like milling_speed or d50 in standard 
    entries. This function attempts to search for relevant entries but 
    will likely return an empty list or limited data if the specific 
    experimental metadata is not indexed.
    
    CRITICAL: This function does NOT generate synthetic data. If the API 
    returns no results or fails, it returns an empty list and logs a warning.
    """
    if query_terms is None:
        query_terms = ["ball milling", "milling"]
    
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": api_key or os.getenv("MP_API_KEY", "")
    }
    
    if not headers["X-API-Key"]:
        logger.warning("Materials Project API key not found. Skipping fetch.")
        return []

    results = []
    
    # Attempt to search for documents containing ball milling keywords
    # Note: The MP API search endpoint might not support full-text search 
    # on abstracts in the way required for this specific scientific domain.
    # We attempt a search but expect potential emptiness.
    try:
        # Try searching via the search endpoint if available, otherwise fallback to known structure
        # Since specific ball milling parameters are rare in standard MP entries,
        # we simulate a query structure but expect limited real-world success 
        # without a dedicated experimental database.
        
        # Construct a query for the search API
        search_payload = {
            "keywords": query_terms,
            "limit": 100
        }
        
        # The MP API search structure varies; if this specific endpoint isn't 
        # available or returns 404, we catch it and return empty list.
        # We do NOT fallback to synthetic data.
        resp = requests.post(
            MP_SEARCH_URL,
            json=search_payload,
            headers=headers,
            timeout=30
        )
        
        if resp.status_code == 200:
            data = resp.json()
            if "results" in data:
                for item in data["results"]:
                    # Map MP fields to our schema if possible. 
                    # Most MP entries will NOT have milling_speed, d50, etc.
                    # We only add if we can reasonably map, otherwise skip.
                    # Since MP is primarily DFT, experimental milling data is unlikely.
                    # We return empty if we can't map real experimental data.
                    # This ensures we don't pollute the dataset with DFT data 
                    # pretending to be milling experiments.
                    logger.info(f"Found MP entry: {item.get('material_id', 'unknown')}")
                    # Placeholder for actual mapping logic if MP had this data.
                    # In reality, MP does not contain 'milling_speed' or 'd50' for standard entries.
                    # So we effectively return empty to avoid fake data.
                    pass 
        elif resp.status_code == 404:
            logger.warning("Materials Project search endpoint not found or no results.")
        else:
            logger.warning(f"Materials Project API returned status {resp.status_code}")
            
    except requests.exceptions.RequestException as e:
        logger.warning(f"Materials Project fetch failed: {e}")
        return []
    
    # Since MP likely doesn't have the specific experimental milling data required,
    # and we must not fabricate, we return an empty list if no valid experimental 
    # rows were found.
    # If the API actually returned experimental data (unlikely), we would populate 'results'.
    # For now, to be safe and real-data compliant, we ensure we don't invent data.
    return results

def save_to_json(data: List[Dict[str, Any]], output_path: str) -> None:
    """Save data to a JSON file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def run_materials_project_ingestion(output_path: str = "data/raw/materials_project_raw.json") -> int:
    """
    Run the Materials Project ingestion pipeline.
    
    Returns:
        int: Number of rows fetched.
    """
    logger.info("Starting Materials Project ingestion...")
    
    # Fetch data
    data = fetch_materials_project_data()
    
    if not data:
        logger.warning("Source skipped: Materials Project (no rows or error)")
        # Create an empty file to indicate the run happened but yielded nothing
        # This allows the pipeline to continue without synthetic data.
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump([], f)
        return 0
    
    # Save data
    save_to_json(data, output_path)
    logger.info(f"Saved {len(data)} rows to {output_path}")
    return len(data)
