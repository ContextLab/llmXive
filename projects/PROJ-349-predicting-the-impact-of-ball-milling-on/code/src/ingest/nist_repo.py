"""
NIST Repository Downloader for Ball Milling Data.

This module implements the ingestion logic for the NIST Search API to find
and download ball milling datasets. It strictly adheres to the "Real Data Only"
policy: if the real API fetch fails or returns no data, it logs a warning and
skips the source without falling back to synthetic data.

Output: data/raw/nist_raw.json
"""

import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from src.utils.logger import get_module_logger
from src.utils.exceptions import DataIngestionError

# Configure logger
logger = get_module_logger(__name__)

# NIST Search API Configuration
NIST_SEARCH_URL = "https://data.nist.gov/api/v1/search"
OUTPUT_DIR = Path("data/raw")
OUTPUT_FILE = OUTPUT_DIR / "nist_raw.json"
CHUNK_SIZE = 100  # Number of results to fetch per page

def fetch_nist_datasets(query: str = "ball milling AND datasetType:csv", max_results: int = 500) -> List[Dict[str, Any]]:
    """
    Fetch ball milling datasets from NIST Search API with pagination.

    Args:
        query: Search query string.
        max_results: Maximum number of results to fetch.

    Returns:
        List of dataset metadata dictionaries.

    Raises:
        DataIngestionError: If the API call fails completely (no data returned).
    """
    all_datasets = []
    offset = 0

    while len(all_datasets) < max_results:
        params = {
            "q": query,
            "limit": CHUNK_SIZE,
            "offset": offset,
            "format": "json"
        }

        try:
            logger.info(f"Fetching NIST datasets: offset={offset}, limit={CHUNK_SIZE}")
            response = requests.get(NIST_SEARCH_URL, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            results = data.get("results", [])
            if not results:
                logger.info("No more results found from NIST.")
                break

            all_datasets.extend(results)
            logger.info(f"Retrieved {len(results)} datasets. Total so far: {len(all_datasets)}")

            # Check if there are more pages
            total_count = data.get("totalResults", 0)
            if len(all_datasets) >= total_count:
                break

            offset += CHUNK_SIZE
            time.sleep(0.5)  # Rate limiting

        except requests.exceptions.RequestException as e:
            logger.warning(f"Error fetching NIST datasets at offset {offset}: {e}")
            # If we have fetched some data so far, we can continue or break depending on policy.
            # Per task: "If the search returns 0 results or the fetch fails... skip this source."
            # However, if we already have some, we might want to keep what we have?
            # The task says "Download the first valid CSV/JSON found" but also "Iterate... to find".
            # Strict interpretation: If the *initial* fetch fails, skip. If partial, we might have data.
            # But to be safe and avoid partial corruption, if the loop breaks early due to error,
            # and we have 0 rows, we skip. If we have rows, we return them.
            if len(all_datasets) == 0:
                raise DataIngestionError(f"NIST API fetch failed with 0 results: {e}")
            logger.warning(f"Returning {len(all_datasets)} partial results due to fetch error.")
            break

    return all_datasets

def download_dataset_file(url: str, timeout: int = 60) -> Optional[Dict[str, Any]]:
    """
    Download a single dataset file (CSV/JSON) from a given URL.

    Args:
        url: Direct download link.
        timeout: Request timeout.

    Returns:
        Parsed data dictionary if successful, None otherwise.
    """
    try:
        logger.info(f"Downloading dataset from: {url}")
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()

        # Determine content type
        content_type = response.headers.get("Content-Type", "").lower()

        if "application/json" in content_type:
            return response.json()
        elif "text/csv" in content_type:
            # Parse CSV manually or use pandas if available (keep dependency light here)
            # For robustness, we'll try to parse simple CSV into a list of dicts
            import csv
            from io import StringIO
            csv_content = StringIO(response.text)
            reader = csv.DictReader(csv_content)
            rows = list(reader)
            return {"rows": rows, "format": "csv"}
        else:
            logger.warning(f"Unsupported content type: {content_type} for {url}")
            return None

    except Exception as e:
        logger.error(f"Failed to download dataset from {url}: {e}")
        return None

def extract_ball_milling_data(dataset: Dict[str, Any], source_id: str) -> List[Dict[str, Any]]:
    """
    Extract relevant ball milling fields from a NIST dataset entry.

    Args:
        dataset: Raw dataset metadata/content.
        source_id: The NIST dataset ID or DOI.

    Returns:
        List of standardized row dictionaries.
    """
    extracted_rows = []

    # Handle JSON structure
    if isinstance(dataset, dict):
        rows = dataset.get("rows", []) if "rows" in dataset else [dataset]
    elif isinstance(dataset, list):
        rows = dataset
    else:
        return []

    for row in rows:
        if not isinstance(row, dict):
            continue

        # Map fields (NIST schema might vary, we look for common keys)
        # Expected keys: milling_speed, milling_time, ball_to_powder_ratio, d10, d50, d90, material_type, etc.
        # Since NIST schema is not fixed, we extract what we can and fill others with NaN.

        new_row = {
            "source_name": "NIST",
            "source_id": source_id,
            "milling_speed": row.get("milling_speed"),
            "milling_time": row.get("milling_time"),
            "ball_to_powder_ratio": row.get("ball_to_powder_ratio"),
            "material_type": row.get("material_type"),
            "d10": row.get("d10"),
            "d50": row.get("d50"),
            "d90": row.get("d90"),
            "youngs_modulus": row.get("youngs_modulus"),
            "density": row.get("density"),
            "process_duration": row.get("process_duration")
        }

        # CRITICAL: Filter out rows without source_id
        if not new_row["source_id"]:
            logger.warning(f"Row filtered: missing source_id in NIST data")
            continue

        # Filter out rows where ALL target/predictor fields are null (optional but good practice)
        # For now, we keep them as the imputation step will handle NaNs.
        extracted_rows.append(new_row)

    return extracted_rows

def run_nist_ingestion() -> List[Dict[str, Any]]:
    """
    Main ingestion function for NIST repository.

    Returns:
        List of extracted and validated data rows.
    """
    logger.info("Starting NIST repository ingestion...")

    try:
        # 1. Search for datasets
        datasets = fetch_nist_datasets()

        if not datasets:
            logger.warning("Source skipped: NIST (no rows or error)")
            return []

        all_rows = []

        # 2. Iterate and download
        for dataset_meta in datasets:
            dataset_id = dataset_meta.get("datasetId") or dataset_meta.get("id") or dataset_meta.get("doi")
            if not dataset_id:
                logger.warning("Skipping dataset entry: missing ID")
                continue

            # Find download link
            download_url = None
            if "downloadUrl" in dataset_meta:
                download_url = dataset_meta["downloadUrl"]
            elif "links" in dataset_meta:
                # Look for a link with 'download' or 'csv' or 'json'
                for link in dataset_meta["links"]:
                    if isinstance(link, dict):
                        if "download" in link.get("rel", "").lower() or link.get("type", "").lower() in ["text/csv", "application/json"]:
                            download_url = link.get("url")
                            break

            if not download_url:
                logger.warning(f"No download URL found for dataset {dataset_id}")
                continue

            # 3. Download and parse
            content = download_dataset_file(download_url)
            if content:
                rows = extract_ball_milling_data(content, dataset_id)
                all_rows.extend(rows)
                logger.info(f"Extracted {len(rows)} rows from dataset {dataset_id}")
            else:
                logger.warning(f"Failed to parse content for dataset {dataset_id}")

        if not all_rows:
            logger.warning("Source skipped: NIST (no rows or error)")
            return []

        logger.info(f"NIST ingestion complete. Total rows: {len(all_rows)}")
        return all_rows

    except Exception as e:
        logger.error(f"NIST ingestion failed: {e}")
        logger.warning("Source skipped: NIST (no rows or error)")
        return []

def save_to_json(data: List[Dict[str, Any]], filepath: Path) -> None:
    """Save data to a JSON file."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)
    logger.info(f"Saved {len(data)} rows to {filepath}")

def main():
    """Entry point for script execution."""
    os.chdir(Path(__file__).resolve().parent.parent.parent)  # Ensure we are at project root
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    data = run_nist_ingestion()
    if data:
        save_to_json(data, OUTPUT_FILE)
    else:
        # Even if no data, we might want to create an empty file or skip?
        # Task says "output file path is defined". Let's create empty if no data to be safe for downstream.
        save_to_json([], OUTPUT_FILE)
        logger.info("Created empty output file due to no data.")

if __name__ == "__main__":
    main()