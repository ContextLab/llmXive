"""
NIST Repository Downloader for Ball Milling Data.

This module implements the ingestion logic for the NIST Search API to find
and download ball milling datasets. It adheres to the strict requirement
of using real data only, with no synthetic fallbacks.
"""

import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
import pandas as pd

from src.utils.logger import get_module_logger
from src.utils.seed import get_seed

# Initialize logger
logger = get_module_logger(__name__)

# Constants
NIST_SEARCH_API = "https://api.nist.gov/datasets/search"
OUTPUT_PATH = Path("data/raw/nist_repo_raw.json")
TIMEOUT_SECONDS = 30
MAX_RETRIES = 3
RETRY_DELAY = 2

def _fetch_search_results(query: str, page: int = 1, page_size: int = 10) -> Optional[Dict[str, Any]]:
    """
    Fetch search results from the NIST Search API.

    Args:
        query: The search query string.
        page: The page number to fetch.
        page_size: Number of results per page.

    Returns:
        A dictionary containing the search results, or None if the request fails.
    """
    params = {
        "q": query,
        "page": page,
        "page_size": page_size
    }

    for attempt in range(MAX_RETRIES):
        try:
            logger.info(f"Fetching NIST search results (Page {page}, Attempt {attempt + 1})...")
            response = requests.get(NIST_SEARCH_API, params=params, timeout=TIMEOUT_SECONDS)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            logger.warning(f"NIST API timeout on attempt {attempt + 1}. Retrying...")
            time.sleep(RETRY_DELAY)
        except requests.exceptions.RequestException as e:
            logger.error(f"NIST API request failed: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode NIST API response: {e}")
            return None

    logger.error(f"Failed to fetch NIST search results after {MAX_RETRIES} attempts.")
    return None

def _download_dataset_file(url: str, dataset_id: str) -> Optional[Dict[str, Any]]:
    """
    Download a dataset file from a given URL and parse it.

    Args:
        url: The direct download URL for the dataset.
        dataset_id: The ID of the dataset for logging and traceability.

    Returns:
        A list of records extracted from the dataset, or None if download/parsing fails.
    """
    try:
        logger.info(f"Downloading dataset {dataset_id} from {url}...")
        response = requests.get(url, timeout=TIMEOUT_SECONDS)
        response.raise_for_status()

        content_type = response.headers.get("Content-Type", "")
        content = response.content

        if "application/json" in content_type or url.endswith(".json"):
            data = response.json()
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                # Assume the data is in a specific key, try common ones
                if "data" in data:
                    return data["data"]
                elif "results" in data:
                    return data["results"]
                else:
                    return [data]
            else:
                logger.warning(f"Unexpected JSON structure for dataset {dataset_id}")
                return None
        elif "text/csv" in content_type or url.endswith(".csv"):
            # Use pandas to read CSV from string
            df = pd.read_csv(pd.io.common.BytesIO(content))
            return df.to_dict(orient="records")
        else:
            logger.warning(f"Unsupported content type {content_type} for dataset {dataset_id}")
            return None

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download dataset {dataset_id}: {e}")
        return None
    except (json.JSONDecodeError, pd.errors.EmptyDataError, pd.errors.ParserError) as e:
        logger.error(f"Failed to parse dataset {dataset_id}: {e}")
        return None

def _normalize_schema(records: List[Dict[str, Any]], source_id: str) -> List[Dict[str, Any]]:
    """
    Normalize records to the project's schema and add traceability metadata.

    Args:
        records: List of raw records.
        source_id: The source ID for the dataset.

    Returns:
        List of normalized records.
    """
    normalized = []
    for record in records:
        if not isinstance(record, dict):
            continue

        # Filter out records without required traceability fields if they exist in the source
        # The task requires recording source_name and source_id for every row.
        # We add them explicitly.
        record["source_name"] = "NIST"
        record["source_id"] = source_id

        # Check for critical missing fields that might indicate a bad row (optional filtering)
        # The task says: "If a row lacks source_id, it MUST be filtered out".
        # Since we just added it, this check is implicitly passed, but we ensure the record is valid.
        if not record.get("source_id"):
            logger.warning(f"Row filtered: missing traceability metadata (source_id)")
            continue

        normalized.append(record)

    return normalized

def run_nist_ingestion() -> List[Dict[str, Any]]:
    """
    Main function to run the NIST ingestion pipeline.

    Returns:
        A list of successfully fetched and normalized records.
    """
    all_records = []
    query = "ball+milling AND datasetType:csv"
    page = 1
    found_valid_dataset = False

    while not found_valid_dataset and page <= 5: # Limit pages to avoid endless loops
        results = _fetch_search_results(query, page=page)
        if not results:
            logger.warning("Source skipped: NIST (no rows or error)")
            return []

        datasets = results.get("results", [])
        if not datasets:
            logger.info(f"No results found on page {page}.")
            page += 1
            continue

        for dataset in datasets:
            dataset_id = dataset.get("id") or dataset.get("datasetId") or dataset.get("doi")
            if not dataset_id:
                logger.warning(f"Skipping dataset entry due to missing ID: {dataset}")
                continue

            # Look for download URLs
            download_url = None
            links = dataset.get("links", [])
            for link in links:
                if link.get("rel") == "self" or link.get("rel") == "download":
                    download_url = link.get("href")
                    break

            if not download_url:
                # Try to find a direct link in the dataset metadata if 'links' is empty
                # This is a fallback heuristic for different API structures
                if "downloadUrl" in dataset:
                    download_url = dataset["downloadUrl"]
                elif "url" in dataset:
                    download_url = dataset["url"]

            if download_url:
                data = _download_dataset_file(download_url, dataset_id)
                if data:
                    logger.info(f"Successfully downloaded {len(data)} records from dataset {dataset_id}")
                    normalized_data = _normalize_schema(data, dataset_id)
                    all_records.extend(normalized_data)
                    found_valid_dataset = True
                    break # Stop after finding the first valid dataset as per task description
            else:
                logger.warning(f"No download URL found for dataset {dataset_id}")

        if not found_valid_dataset:
            page += 1

    if not all_records:
        logger.warning("Source skipped: NIST (no rows or error)")
        return []

    return all_records

def save_to_csv(data: List[Dict[str, Any]], output_path: Optional[Path] = None) -> None:
    """
    Save the fetched data to a CSV file.

    Args:
        data: List of records.
        output_path: Path to the output CSV file.
    """
    if not output_path:
        output_path = OUTPUT_PATH

    if not data:
        logger.warning("No data to save.")
        return

    df = pd.DataFrame(data)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(data)} records to {output_path}")

def save_to_json(data: List[Dict[str, Any]], output_path: Optional[Path] = None) -> None:
    """
    Save the fetched data to a JSON file.

    Args:
        data: List of records.
        output_path: Path to the output JSON file.
    """
    if not output_path:
        output_path = OUTPUT_PATH.with_suffix(".json")

    if not data:
        logger.warning("No data to save.")
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    logger.info(f"Saved {len(data)} records to {output_path}")

def main():
    """Entry point for the NIST ingestion script."""
    logger.info("Starting NIST repository ingestion...")
    data = run_nist_ingestion()

    if data:
        # Save to JSON as primary format for ingestion pipeline
        save_to_json(data, OUTPUT_PATH)
        # Also save to CSV for easy inspection
        save_to_csv(data, OUTPUT_PATH.with_suffix(".csv"))
    else:
        logger.warning("NIST ingestion completed with no data.")

if __name__ == "__main__":
    main()