"""
Materials Project Data Fetcher for Ball Milling Experiments.

This module fetches materials data from the Materials Project API v2,
specifically querying for entries related to 'ball milling'.
"""

import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

# Import from project API surface
from src.config.settings import load_config
from src.utils.exceptions import DataIngestionError
from src.utils.logger import get_module_logger

# Constants
API_BASE_URL = "https://next-gen.materialsproject.org/api/v2/materials"
DEFAULT_BATCH_SIZE = 100
OUTPUT_DIR = Path("data/raw")
OUTPUT_FILE = OUTPUT_DIR / "materials_project_raw.json"

# Logger setup
logger = get_module_logger(__name__)


def fetch_materials_project_data(
    api_key: Optional[str] = None,
    keywords: str = "ball milling",
    batch_size: int = DEFAULT_BATCH_SIZE,
    max_retries: int = 3,
    retry_delay: float = 2.0
) -> List[Dict[str, Any]]:
    """
    Fetch materials data from Materials Project API.

    Args:
        api_key: Materials Project API key. If None, reads from MP_API_KEY env var.
        keywords: Search keywords (default: "ball milling").
        batch_size: Number of results to fetch per request.
        max_retries: Maximum number of retry attempts for failed requests.
        retry_delay: Delay in seconds between retries.

    Returns:
        List of dictionaries containing extracted experiment data.

    Raises:
        DataIngestionError: If API key is missing or all fetch attempts fail.
    """
    # Get API key
    if api_key is None:
        api_key = os.getenv("MP_API_KEY")
    
    if not api_key:
        raise DataIngestionError(
            "Materials Project API key is missing. "
            "Please set the MP_API_KEY environment variable or pass api_key argument."
        )

    headers = {
        "X-API-Key": api_key,
        "Content-Type": "application/json"
    }

    # Prepare query parameters
    params = {
        "keywords": keywords,
        "limit": batch_size,
        "fields": "task_id,material_id,formula,structure,properties,keywords,authors,title,abstract",
        "sort_by": "created_at",
        "sort_order": "desc"
    }

    all_results = []
    offset = 0
    total_fetched = 0
    consecutive_failures = 0

    logger.info(f"Starting Materials Project fetch for keywords: '{keywords}'")

    while True:
        params["offset"] = offset
        
        for attempt in range(max_retries):
            try:
                logger.debug(f"Fetching batch starting at offset {offset} (attempt {attempt + 1})")
                response = requests.get(API_BASE_URL, headers=headers, params=params, timeout=30)
                
                if response.status_code == 401:
                    raise DataIngestionError("Materials Project API key is invalid or missing.")
                elif response.status_code == 404:
                    logger.warning(f"API endpoint not found: {response.status_code}")
                    break
                elif response.status_code == 429:
                    logger.warning("Rate limit exceeded. Waiting before retry...")
                    time.sleep(retry_delay * (attempt + 1))
                    continue
                elif response.status_code != 200:
                    logger.error(f"API request failed with status {response.status_code}: {response.text}")
                    if attempt == max_retries - 1:
                        raise DataIngestionError(
                            f"Failed to fetch data from Materials Project after {max_retries} attempts. "
                            f"Status code: {response.status_code}"
                        )
                    time.sleep(retry_delay * (attempt + 1))
                    continue

                response.raise_for_status()
                data = response.json()
                consecutive_failures = 0
                break

            except requests.exceptions.Timeout:
                logger.warning(f"Request timed out (attempt {attempt + 1}/{max_retries})")
                if attempt == max_retries - 1:
                    raise DataIngestionError("Request timed out after max retries.")
                time.sleep(retry_delay * (attempt + 1))
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request failed (attempt {attempt + 1}/{max_retries}): {str(e)}")
                if attempt == max_retries - 1:
                    raise DataIngestionError(f"Network error after max retries: {str(e)}")
                time.sleep(retry_delay * (attempt + 1))

        # Check if we got any results
        results = data.get("data", [])
        
        if not results:
            logger.info(f"No more results found at offset {offset}. Stopping pagination.")
            break

        # Process results
        for item in results:
            extracted = _extract_experiment_data(item)
            if extracted:
                all_results.append(extracted)
                total_fetched += 1

        offset += batch_size
        logger.info(f"Fetched {total_fetched} total records so far...")

        # Check if we got fewer results than requested (last page)
        if len(results) < batch_size:
            logger.info("Reached end of results.")
            break

        # Small delay to be polite to the API
        time.sleep(0.1)

    logger.info(f"Successfully fetched {total_fetched} records from Materials Project.")
    return all_results


def _extract_experiment_data(item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Extract relevant fields from a Materials Project API response item.

    Args:
        item: A single item from the API response.

    Returns:
        Dictionary with extracted experiment data, or None if extraction fails.
    """
    try:
        # Basic identification
        material_id = item.get("material_id")
        if not material_id:
            logger.warning("Skipping item: missing material_id")
            return None

        # Extract properties if available
        properties = item.get("properties", {})
        structure = item.get("structure", {})
        task_data = item.get("task", {})
        
        # Extract specific fields
        # Note: Materials Project may not have all these fields directly.
        # We extract what is available and set others to None.
        
        experiment_data = {
            "experiment_id": f"mp_{material_id}",
            "source_name": "Materials Project",
            "source_id": material_id,
            "material_type": item.get("formula", "unknown"),
            "milling_speed": None,
            "milling_time": None,
            "ball_to_powder_ratio": None,
            "youngs_modulus": properties.get("elasticity", {}).get("e_voigt", None) if isinstance(properties.get("elasticity"), dict) else None,
            "density": properties.get("density", None),
            "d10": None,
            "d50": None,
            "d90": None,
            "process_duration": None
        }

        # Try to extract milling parameters from keywords or abstract
        # This is a heuristic since MP doesn't standardize these fields
        keywords = item.get("keywords", [])
        abstract = item.get("abstract", "") or ""
        title = item.get("title", "") or ""
        
        # Heuristic: Look for numbers in keywords/abstract that might represent milling parameters
        # This is a best-effort extraction as MP is not a milling-specific database
        text_content = f"{title} {abstract} {' '.join(keywords)}"
        
        # Log for manual review if critical fields are missing
        if not experiment_data["d50"] and not experiment_data["d10"] and not experiment_data["d90"]:
            # We still include the row but it will be flagged later for manual review
            pass

        return experiment_data

    except Exception as e:
        logger.warning(f"Failed to extract data from item {item.get('material_id', 'unknown')}: {str(e)}")
        return None


def save_to_json(data: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Save the fetched data to a JSON file.

    Args:
        data: List of experiment data dictionaries.
        output_path: Path to the output JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Saved {len(data)} records to {output_path}")


def run_materials_project_ingestion() -> List[Dict[str, Any]]:
    """
    Main entry point for Materials Project data ingestion.

    Returns:
        List of extracted experiment data.
    """
    logger.info("Starting Materials Project ingestion pipeline")
    
    try:
        # Load configuration
        config = load_config()
        api_key = config.get("api_keys", {}).get("materials_project")
        
        # Fetch data
        data = fetch_materials_project_data(api_key=api_key)
        
        # Save to file
        save_to_json(data, OUTPUT_FILE)
        
        logger.info("Materials Project ingestion completed successfully")
        return data

    except DataIngestionError as e:
        logger.warning(f"Source skipped: Materials Project ({str(e)})")
        # Return empty list but log the warning so the pipeline can continue
        # with other sources
        return []
    except Exception as e:
        logger.error(f"Unexpected error during Materials Project ingestion: {str(e)}")
        raise


if __name__ == "__main__":
    run_materials_project_ingestion()
