import os
import sys
import json
import logging
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
import requests

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

def ensure_output_dir(output_dir: Path) -> None:
    """Create the output directory if it does not exist."""
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured output directory exists: {output_dir}")

def fetch_datasets_page(page: int = 1, page_size: int = 100) -> Optional[Dict[str, Any]]:
    """
    Fetch a page of datasets from the OpenNeuro GraphQL API.
    Returns the JSON response or None if the request fails.
    """
    url = "https://api.openneuro.org/datasets"
    params = {
        "first": page_size,
        "after": None,
        "orderBy": "created",
        "sortOrder": "DESC"
    }
    
    # OpenNeuro API v4 endpoint for listing datasets
    # Note: The GraphQL endpoint is preferred for complex queries, 
    # but the REST listing is simpler for initial index fetching.
    # Using the GraphQL endpoint to search for specific keywords directly is more efficient.
    
    graphql_query = """
    query GetDatasets($first: Int!, $after: String) {
      datasets(first: $first, after: $after) {
        edges {
          node {
            id
            name
            description
            created
            uploader {
              id
              name
            }
            latestSnapshot {
              id
              summary {
                modalities
                totalSubjects
              }
              description {
                Name
                Version
                Funding
                ReferencesAndLinks
              }
              id
            }
          }
          cursor
        }
        pageInfo {
          hasNextPage
          hasPreviousPage
          startCursor
          endCursor
        }
      }
    }
    """
    
    headers = {"Content-Type": "application/json"}
    payload = {
        "query": graphql_query,
        "variables": {
            "first": page_size,
            "after": None
        }
    }

    try:
        logger.info(f"Fetching OpenNeuro datasets page...")
        response = requests.post(
            "https://api.openneuro.org/graphql",
            json=payload,
            headers=headers,
            timeout=60
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch OpenNeuro datasets page: {e}")
        return None

def fetch_full_index() -> Optional[List[Dict[str, Any]]]:
    """
    Fetch the full index of datasets from OpenNeuro.
    Returns a list of dataset dictionaries or None if the request fails.
    """
    all_datasets = []
    cursor = None
    page = 1
    
    while True:
        graphql_query = """
        query GetDatasets($first: Int!, $after: String) {
          datasets(first: $first, after: $after) {
            edges {
              node {
                id
                name
                description
                created
                uploader {
                  id
                  name
                }
                latestSnapshot {
                  id
                  summary {
                    modalities
                    totalSubjects
                  }
                  description {
                    Name
                    Version
                    Funding
                    ReferencesAndLinks
                  }
                  id
                }
              }
              cursor
            }
            pageInfo {
              hasNextPage
              hasPreviousPage
              startCursor
              endCursor
            }
          }
        }
        """
        
        headers = {"Content-Type": "application/json"}
        payload = {
            "query": graphql_query,
            "variables": {
                "first": 100,
                "after": cursor
            }
        }

        try:
            logger.info(f"Fetching OpenNeuro datasets page {page}...")
            response = requests.post(
                "https://api.openneuro.org/graphql",
                json=payload,
                headers=headers,
                timeout=60
            )
            response.raise_for_status()
            data = response.json()
            
            if "errors" in data:
                logger.error(f"OpenNeuro API returned errors: {data['errors']}")
                return None

            datasets_page = data.get("data", {}).get("datasets", {}).get("edges", [])
            if not datasets_page:
                break
            
            for edge in datasets_page:
                all_datasets.append(edge["node"])
            
            page_info = data.get("data", {}).get("datasets", {}).get("pageInfo", {})
            if not page_info.get("hasNextPage", False):
                break
            
            cursor = page_info.get("endCursor")
            page += 1
            
            # Rate limiting precaution
            time.sleep(0.5)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch OpenNeuro datasets page {page}: {e}")
            # Log error but do not exit; return what we have if any
            if all_datasets:
                logger.warning("Returning partial index due to network error.")
                return all_datasets
            return None

    logger.info(f"Successfully fetched {len(all_datasets)} datasets from OpenNeuro.")
    return all_datasets

def filter_datasets(datasets: List[Dict[str, Any]], keywords: List[str]) -> List[Dict[str, Any]]:
    """
    Filter datasets based on keywords in name or description.
    Keywords: 'TSST', 'heartbeat', 'interoception'
    """
    filtered = []
    keywords_lower = [k.lower() for k in keywords]
    
    for dataset in datasets:
        name = dataset.get("name", "").lower()
        desc = dataset.get("description", {}).get("Name", "").lower() if dataset.get("description") else ""
        # Check latestSnapshot description if available
        snapshot_desc = ""
        if dataset.get("latestSnapshot") and dataset["latestSnapshot"].get("description"):
            snapshot_desc = dataset["latestSnapshot"]["description"].get("Name", "").lower()
        
        combined_text = f"{name} {desc} {snapshot_desc}"
        
        if any(kw in combined_text for kw in keywords_lower):
            filtered.append(dataset)
            logger.info(f"Found matching dataset: {dataset.get('id')} - {dataset.get('name')}")
    
    return filtered

def save_index(datasets: List[Dict[str, Any]], output_path: Path) -> None:
    """Save the filtered dataset index to a JSON file."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(datasets, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved filtered index to {output_path}")

def main() -> None:
    """
    Main entry point for downloading the OpenNeuro index.
    Downloads metadata for studies containing 'TSST', 'heartbeat', or 'interoception'.
    If download fails, logs error but does NOT exit (allows pipeline to continue).
    """
    output_dir = Path("data/raw/openneuro")
    output_file = output_dir / "index.json"
    
    logger.info("Starting OpenNeuro index download task (T010b).")
    
    try:
        ensure_output_dir(output_dir)
        
        # Fetch full index
        full_index = fetch_full_index()
        
        if full_index is None:
            logger.error("Failed to fetch OpenNeuro index. Pipeline will continue to local scan.")
            # Create an empty index file to indicate failure state for downstream tasks
            save_index([], output_file)
            return
        
        # Filter for relevant keywords
        keywords = ["TSST", "heartbeat", "interoception"]
        filtered_datasets = filter_datasets(full_index, keywords)
        
        logger.info(f"Found {len(filtered_datasets)} datasets matching keywords.")
        
        # Save the filtered index
        save_index(filtered_datasets, output_file)
        
        logger.info("OpenNeuro index download completed successfully.")
        
    except Exception as e:
        logger.error(f"Unexpected error during OpenNeuro index download: {e}")
        # Ensure we don't crash the pipeline
        save_index([], output_file)

if __name__ == "__main__":
    main()
