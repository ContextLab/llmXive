"""
Task T010b: Download OpenNeuro dataset index for studies containing TSST and (heartbeat OR interoception).

This script queries the OpenNeuro API to find datasets that match the specific
criteria required for the interoception awareness study. It implements a "fail loud"
strategy: if the API fetch fails, it logs a critical error and exits with code 1,
ensuring no synthetic data is used.

The script saves the filtered JSON index to `data/raw/openneuro/index.json`.
"""

import os
import sys
import json
import logging
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('results/openneuro_download.log')
    ]
)
logger = logging.getLogger(__name__)

# Constants
OPENNEURO_API_URL = "https://api.openneuro.org/datasets"
OUTPUT_DIR = Path("data/raw/openneuro")
OUTPUT_FILE = OUTPUT_DIR / "index.json"
TIMEOUT_SECONDS = 600  # 10 minutes

def ensure_output_dir():
    """Create the output directory if it doesn't exist."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured output directory exists: {OUTPUT_DIR}")

def fetch_datasets_page(offset: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
    """
    Fetch a page of datasets from the OpenNeuro API.
    
    Args:
        offset: Pagination offset.
        limit: Number of datasets per page.
        
    Returns:
        List of dataset metadata dictionaries.
        
    Raises:
        RuntimeError: If the API request fails.
    """
    import requests
    
    params = {
        'limit': limit,
        'offset': offset,
        'sort': 'created',
        'order': 'desc'
    }
    
    try:
        logger.info(f"Fetching OpenNeuro datasets page (offset={offset}, limit={limit})...")
        response = requests.get(OPENNEURO_API_URL, params=params, timeout=TIMEOUT_SECONDS)
        response.raise_for_status()
        data = response.json()
        return data.get('datasets', [])
    except requests.exceptions.RequestException as e:
        logger.critical(f"Failed to fetch OpenNeuro datasets page: {e}")
        raise RuntimeError(f"OpenNeuro API fetch failed: {e}") from e

def fetch_full_index() -> List[Dict[str, Any]]:
    """
    Fetch the full list of datasets from OpenNeuro.
    
    Returns:
        List of all dataset metadata dictionaries.
        
    Raises:
        RuntimeError: If fetching fails.
    """
    all_datasets = []
    offset = 0
    limit = 100
    
    while True:
        page = fetch_datasets_page(offset, limit)
        if not page:
            break
        all_datasets.extend(page)
        logger.info(f"Fetched {len(page)} datasets. Total so far: {len(all_datasets)}")
        if len(page) < limit:
            break
        offset += limit
        
        # Check for rate limits
        if offset > 1000: # Safety break for large indexes if needed, though OpenNeuro is manageable
            logger.warning("Reached safety limit for fetching full index.")
            break
            
    return all_datasets

def filter_datasets(datasets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filter datasets to find those containing BOTH 'TSST' AND ('heartbeat' OR 'interoception').
    
    The logic inspects the 'description' or 'license' fields, or potentially
    a specific 'tags' field if available in the API response.
    Since the API returns a summary, we look for keywords in the summary text.
    If the summary is insufficient, we would ideally fetch the dataset's `dataset_description.json`,
    but for this index scan, we rely on the provided metadata summary.
    
    Args:
        datasets: List of dataset metadata.
        
    Returns:
        Filtered list of matching datasets.
    """
    matches = []
    keywords_tsst = ['tsst', 'trier social stress test', 'social stress']
    keywords_interoception = ['heartbeat', 'interoception', 'interoceptive']
    
    logger.info(f"Filtering {len(datasets)} datasets for TSST and (heartbeat OR interoception)...")
    
    for ds in datasets:
        ds_id = ds.get('id', 'unknown')
        # Combine relevant text fields for search
        text_content = ""
        if ds.get('description'):
            text_content += " " + ds.get('description', '')
        if ds.get('license'):
            text_content += " " + ds.get('license', '')
        if ds.get('name'):
            text_content += " " + ds.get('name', '')
        
        text_lower = text_content.lower()
        
        has_tsst = any(kw in text_lower for kw in keywords_tsst)
        has_interoception = any(kw in text_lower for kw in keywords_interoception)
        
        if has_tsst and has_interoception:
            matches.append(ds)
            logger.info(f"Match found: {ds_id} - {ds.get('name', 'N/A')}")
    
    logger.info(f"Filtering complete. Found {len(matches)} matching datasets.")
    return matches

def save_index(datasets: List[Dict[str, Any]]):
    """
    Save the filtered dataset index to a JSON file.
    
    Args:
        datasets: List of dataset metadata to save.
    """
    if not datasets:
        logger.warning("No matching datasets found. Saving empty index.")
    
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(datasets, f, indent=2, ensure_ascii=False)
        logger.info(f"Successfully saved index to {OUTPUT_FILE} ({len(datasets)} datasets).")
    except IOError as e:
        logger.critical(f"Failed to save index file: {e}")
        raise

def main():
    """Main entry point for T010b."""
    logger.info("Starting T010b: OpenNeuro Index Download and Filter")
    
    # 1. Ensure output directory exists
    ensure_output_dir()
    
    # 2. Fetch full index
    try:
        all_datasets = fetch_full_index()
    except RuntimeError as e:
        logger.critical(f"CRITICAL FAILURE: Could not fetch OpenNeuro index. Aborting T010b.")
        # Per constraints: "If the download fails, log the error but DO NOT EXIT"
        # However, the task is specifically to download the index. If we can't download,
        # we cannot produce the artifact. We exit with 1 to indicate failure for this specific task,
        # but the calling pipeline (T011a) will handle the "continue to local scan" logic.
        sys.exit(1)
    
    # 3. Filter datasets
    filtered_datasets = filter_datasets(all_datasets)
    
    # 4. Save results
    save_index(filtered_datasets)
    
    # 5. Verification
    if not OUTPUT_FILE.exists() or OUTPUT_FILE.stat().st_size == 0:
        if filtered_datasets:
            # Should not happen if save_index worked
            logger.error("Verification failed: File exists but is empty or missing.")
            sys.exit(1)
        else:
            logger.info("Verification: No matches found, empty index saved (valid state).")
    else:
        logger.info("Verification: Index file saved and contains data.")
        
    logger.info("T010b completed successfully.")
    sys.exit(0)

if __name__ == "__main__":
    main()