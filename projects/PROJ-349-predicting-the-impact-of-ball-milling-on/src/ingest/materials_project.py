import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

from src.config.settings import get_settings
from src.exceptions import DataIngestionError, SourceConnectionError

# Initialize logger
logger = logging.getLogger(__name__)

# Constants
MP_API_BASE_URL = "https://next-gen.materialsproject.org/api/v2/mp"
MP_ENDPOINT = f"{MP_API_BASE_URL}/docs"  # Using docs/search for text queries
OUTPUT_PATH = Path("data/raw/materials_project_raw.json")
QUERY_KEYWORDS = ["ball milling", "milling"]
MAX_RETRIES = 3
RETRY_DELAY = 1.0  # seconds

def _get_api_key() -> str:
    """Retrieve the Materials Project API key from environment variables."""
    api_key = os.getenv("MP_API_KEY")
    if not api_key:
        raise DataIngestionError(
            "Materials Project API key (MP_API_KEY) not found in environment variables."
        )
    return api_key

def fetch_materials_project_data(
    keywords: Optional[List[str]] = None, max_results: int = 100
) -> List[Dict[str, Any]]:
    """
    Fetches ball milling experimental data from the Materials Project API.

    Args:
        keywords: List of keywords to search for (e.g., 'ball milling').
        max_results: Maximum number of entries to fetch.

    Returns:
        A list of dictionaries containing extracted data.

    Raises:
        SourceConnectionError: If the API request fails after retries.
        DataIngestionError: If the API key is missing or data format is invalid.
    """
    if keywords is None:
        keywords = QUERY_KEYWORDS

    api_key = _get_api_key()
    headers = {
        "X-API-Key": api_key,
        "Content-Type": "application/json",
    }

    all_entries = []
    search_query = " OR ".join(keywords)

    # Materials Project Search API endpoint for documents
    # Note: The exact endpoint might vary; using a generic search approach
    # The MP API often requires specific query parameters.
    # Attempting to use the docs endpoint with a text query.
    search_url = f"{MP_API_BASE_URL}/docs/search"
    
    params = {
        "q": search_query,
        "limit": max_results,
        "fields": "material_id,keywords,abstract,task_ids" # Requesting relevant fields
    }

    logger.info(f"Searching Materials Project for: {search_query}")

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(search_url, headers=headers, params=params, timeout=30)
            
            if response.status_code == 401:
                raise SourceConnectionError("Authentication failed: Invalid API Key.")
            elif response.status_code == 403:
                raise SourceConnectionError("Forbidden: API Key does not have access.")
            elif response.status_code == 429:
                if attempt < MAX_RETRIES:
                    logger.warning(f"Rate limited. Retrying in {RETRY_DELAY} seconds...")
                    time.sleep(RETRY_DELAY)
                    continue
                else:
                    raise SourceConnectionError("Rate limit exceeded after retries.")
            elif response.status_code != 200:
                raise SourceConnectionError(
                    f"Request failed with status {response.status_code}: {response.text}"
                )

            data = response.json()
            results = data.get("results", [])

            if not results:
                logger.warning("No results found in the initial search response.")
                return []

            # Process results
            for item in results:
                # Extract relevant fields. Note: MP structure may vary.
                # We attempt to map standard fields to our schema.
                # Since MP is primarily for crystal structures, 'ball milling' data
                # might be sparse or in the 'abstract'/'keywords' only.
                # We extract what is available and log warnings for missing fields.
                
                entry = {
                    "source": "materials_project",
                    "experiment_id": item.get("material_id", f"mp_{time.time()}_{len(all_entries)}"),
                    "keywords": item.get("keywords", []),
                    "abstract": item.get("abstract", ""),
                    # MP doesn't natively have 'milling_speed' etc. in standard material docs.
                    # We must parse the abstract or keywords if present, or set to null.
                    # For this task, we extract structural properties if available, 
                    # and mark process parameters as null if not found in the text.
                    "material_type": item.get("pretty_formula", "unknown"),
                    "youngs_modulus": None, # Not typically in search results, would need detailed calc
                    "density": None,        # Often available as 'density' in material docs
                    "milling_speed": None,
                    "milling_time": None,
                    "ball_to_powder_ratio": None,
                    "d10": None,
                    "d50": None,
                    "d90": None,
                    "process_duration": None
                }

                # Try to populate density if available in the response
                if "density" in item:
                    entry["density"] = item["density"]
                
                # Attempt to parse abstract for numeric values if present
                # This is a basic heuristic; robust parsing belongs in T013b/T014c
                abstract = entry.get("abstract", "")
                if abstract:
                    # Placeholder logic to demonstrate extraction attempt
                    # Real implementation would use regex or NLP
                    pass

                all_entries.append(entry)

            logger.info(f"Successfully fetched {len(all_entries)} entries from Materials Project.")
            return all_entries

        except requests.exceptions.RequestException as e:
            logger.error(f"Request error (Attempt {attempt}/{MAX_RETRIES}): {e}")
            if attempt == MAX_RETRIES:
                raise SourceConnectionError(f"Failed to connect to Materials Project API after {MAX_RETRIES} attempts.") from e
            time.sleep(RETRY_DELAY)
        except json.JSONDecodeError as e:
            raise DataIngestionError("Invalid JSON response from Materials Project API.") from e

    return []

def save_to_json(data: List[Dict[str, Any]], output_path: str) -> None:
    """
    Saves the fetched data to a JSON file.

    Args:
        data: List of dictionaries to save.
        output_path: Path to the output JSON file.
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)
    
    logger.info(f"Saved {len(data)} entries to {output_file}")

def run_materials_project_ingestion() -> Optional[str]:
    """
    Orchestrates the Materials Project data ingestion pipeline.
    
    Returns:
        Path to the output file if successful, None if skipped.
    """
    try:
        logger.info("Starting Materials Project data ingestion...")
        data = fetch_materials_project_data()
        
        if not data:
            logger.warning("Source skipped: Materials Project (no rows or error)")
            return None
        
        save_to_json(data, str(OUTPUT_PATH))
        return str(OUTPUT_PATH)
        
    except SourceConnectionError as e:
        logger.warning(f"Source skipped: Materials Project (no rows or error) - {e}")
        return None
    except DataIngestionError as e:
        logger.warning(f"Source skipped: Materials Project (no rows or error) - {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error during Materials Project ingestion: {e}", exc_info=True)
        logger.warning("Source skipped: Materials Project (no rows or error)")
        return None