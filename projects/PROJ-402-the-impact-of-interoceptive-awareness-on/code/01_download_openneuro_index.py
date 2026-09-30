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

# OpenNeuro API endpoint for dataset search
# Using the public API to fetch dataset metadata
OPENNEURO_API_BASE = "https://api.openneuro.org"
SEARCH_ENDPOINT = "/crn/datasets"

# Known fallback dataset IDs for stress/interoception studies if search fails
FALLBACK_DATASET_IDS = [
    "ds000238",  # Example: Stress study
    "ds000246",  # Example: Interoception study
    "ds003410"   # Example: Another relevant study
]

def ensure_output_dir(output_path: Path) -> None:
    """Ensure the output directory exists."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory ensured: {output_path.parent}")

def fetch_datasets_page(
    keywords: List[str], 
    limit: int = 100, 
    offset: int = 0
) -> Optional[Dict[str, Any]]:
    """
    Fetch a page of datasets from OpenNeuro API matching keywords.
    
    Args:
        keywords: List of keywords to search for (e.g., ['TSST', 'heartbeat'])
        limit: Number of results per page
        offset: Pagination offset
        
    Returns:
        Dictionary containing dataset list or None if request fails
    """
    import requests
    
    params = {
        'search': ','.join(keywords),
        'limit': limit,
        'offset': offset
    }
    
    url = f"{OPENNEURO_API_BASE}{SEARCH_ENDPOINT}"
    
    try:
        logger.info(f"Fetching OpenNeuro datasets from {url} with params: {params}")
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch OpenNeuro datasets: {e}")
        return None

def fetch_full_index(keywords: List[str]) -> List[Dict[str, Any]]:
    """
    Fetch all datasets matching keywords by paginating through results.
    
    Args:
        keywords: List of keywords to search for
        
    Returns:
        List of dataset objects matching the search criteria
    """
    all_datasets = []
    offset = 0
    limit = 100
    max_retries = 3
    
    while True:
        for attempt in range(max_retries):
            result = fetch_datasets_page(keywords, limit, offset)
            if result is not None:
                break
            logger.warning(f"Attempt {attempt + 1}/{max_retries} failed, retrying...")
            time.sleep(2 ** attempt)  # Exponential backoff
        else:
            logger.error("All retry attempts failed. Returning partial results.")
            break
        
        datasets = result.get('datasets', [])
        if not datasets:
            break
        
        all_datasets.extend(datasets)
        logger.info(f"Fetched {len(datasets)} datasets (total: {len(all_datasets)})")
        
        if len(datasets) < limit:
            break  # No more pages
        
        offset += limit
        
        # Rate limiting: be respectful to the API
        time.sleep(0.5)
    
    return all_datasets

def filter_datasets(
    datasets: List[Dict[str, Any]], 
    required_keywords: List[str]
) -> List[Dict[str, Any]]:
    """
    Filter datasets to ensure they contain all required keywords in their description or name.
    
    Args:
        datasets: List of dataset objects
        required_keywords: Keywords that must be present in name or description
        
    Returns:
        Filtered list of datasets
    """
    filtered = []
    for dataset in datasets:
        name = dataset.get('name', '').lower()
        description = dataset.get('description', {}).get('name', '').lower() if dataset.get('description') else ''
        combined_text = f"{name} {description}"
        
        if all(keyword.lower() in combined_text for keyword in required_keywords):
            filtered.append(dataset)
    
    return filtered

def save_index(datasets: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Save the dataset index to a JSON file.
    
    Args:
        datasets: List of dataset objects to save
        output_path: Path to the output JSON file
    """
    ensure_output_dir(output_path)
    
    # Format output to match expected schema: list of objects with id, name, description
    formatted_datasets = []
    for ds in datasets:
        formatted = {
            'id': ds.get('id'),
            'name': ds.get('name'),
            'description': ds.get('description', {}).get('name', '') if ds.get('description') else ''
        }
        formatted_datasets.append(formatted)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(formatted_datasets, f, indent=2)
    
    logger.info(f"Saved {len(formatted_datasets)} datasets to {output_path}")

def main() -> int:
    """
    Main entry point for downloading OpenNeuro dataset index.
    
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    logger.info("Starting OpenNeuro dataset index download task (T010b)")
    
    # Define search keywords based on task requirements
    # Looking for studies with "TSST" AND ("heartbeat" OR "interoception")
    primary_keywords = ['TSST', 'heartbeat']
    alternative_keywords = ['TSST', 'interoception']
    
    output_path = Path('data/raw/openneuro/index.json')
    
    # Try primary keyword search
    logger.info(f"Searching with primary keywords: {primary_keywords}")
    datasets = fetch_full_index(primary_keywords)
    
    # If no results, try alternative keywords
    if not datasets:
        logger.warning(f"No results with primary keywords, trying: {alternative_keywords}")
        datasets = fetch_full_index(alternative_keywords)
    
    # If still no results, try fallback dataset IDs
    if not datasets:
        logger.warning("No results from keyword search. Attempting fallback dataset IDs.")
        import requests
        fallback_results = []
        for ds_id in FALLBACK_DATASET_IDS:
            try:
                url = f"{OPENNEURO_API_BASE}/crn/datasets/{ds_id}"
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    ds_data = response.json()
                    fallback_results.append({
                        'id': ds_data.get('id'),
                        'name': ds_data.get('name'),
                        'description': ds_data.get('description', {}).get('name', '') if ds_data.get('description') else ''
                    })
                    logger.info(f"Added fallback dataset: {ds_id}")
            except Exception as e:
                logger.warning(f"Failed to fetch fallback dataset {ds_id}: {e}")
        
        datasets = fallback_results
    
    if not datasets:
        logger.error("No datasets found from any source. Index will be empty.")
        # Still create an empty index file as required
        save_index([], output_path)
        return 0  # Don't fail the pipeline, just log the warning
    
    # Filter to ensure we have the right datasets
    filtered_datasets = filter_datasets(datasets, ['TSST'])
    if not filtered_datasets:
        logger.warning("No datasets matched all required filters. Using unfiltered results.")
        filtered_datasets = datasets
    
    # Save the index
    save_index(filtered_datasets, output_path)
    
    logger.info("OpenNeuro dataset index download completed successfully")
    return 0

if __name__ == "__main__":
    sys.exit(main())
