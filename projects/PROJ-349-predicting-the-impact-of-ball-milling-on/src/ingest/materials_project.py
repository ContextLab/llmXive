"""
Materials Project Data Fetcher (Task T012).

Fetches ball milling related material data from the Materials Project API v2.
Implements manual chunking, online statistics accumulation, and strict traceability
(source_name, source_id).
"""

import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

# Import from existing project API surface
from src.utils.logger import get_module_logger
from src.utils.seed import get_seed
from src.utils.exceptions import DataIngestionError

# Configuration
API_BASE_URL = "https://next-gen.materialsproject.org/api/v2/materials"
API_KEY = os.getenv("MP_API_KEY")
OUTPUT_PATH = Path("data/raw/materials_project_raw.json")
BATCH_SIZE = 100  # Number of materials to fetch per request
TIMEOUT = 30  # Seconds

logger = get_module_logger(__name__)

def fetch_materials_project_data(
    keywords: str = "ball milling",
    batch_size: int = BATCH_SIZE,
    max_pages: int = 10,
) -> List[Dict[str, Any]]:
    """
    Fetches materials data from Materials Project API with manual chunking.

    Args:
        keywords: Search keyword (default: "ball milling").
        batch_size: Number of items per API request.
        max_pages: Maximum number of pages (batches) to fetch.

    Returns:
        List of extracted material records with traceability metadata.
    """
    if not API_KEY:
        logger.warning("MP_API_KEY not found in environment. Skipping Materials Project fetch.")
        return []

    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json",
    }

    params = {
        "keywords": keywords,
        "page_limit": batch_size,
        "page": 1,
        "fields": "material_id,keywords,abstracts,thermo,structure",
    }

    all_records = []
    total_fetched = 0
    total_filtered = 0

    logger.info(f"Starting fetch from Materials Project with keyword: '{keywords}'")

    for page in range(1, max_pages + 1):
        params["page"] = page
        try:
            logger.debug(f"Fetching page {page}...")
            response = requests.get(API_BASE_URL, headers=headers, params=params, timeout=TIMEOUT)
            response.raise_for_status()
            data = response.json()

            results = data.get("data", [])
            if not results:
                logger.info(f"No more results on page {page}. Stopping pagination.")
                break

            # Process batch
            batch_records = []
            for item in results:
                material_id = item.get("material_id")
                if not material_id:
                    logger.warning(f"Record missing material_id. Skipping.")
                    total_filtered += 1
                    continue

                # Extract relevant fields
                record = {
                    "source_name": "Materials Project",
                    "source_id": material_id,
                    "material_id": material_id,
                    # Note: MP API does not directly expose milling_speed, milling_time, etc.
                    # We extract available properties and flag for potential manual curation
                    # or downstream imputation if missing.
                    "keywords": item.get("keywords", []),
                    "abstract": item.get("abstract", ""),
                    "thermo": item.get("thermo", {}),
                    "structure": item.get("structure", {}),
                    # Placeholder fields for schema compliance (will be imputed if missing)
                    "milling_speed": None,
                    "milling_time": None,
                    "ball_to_powder_ratio": None,
                    "youngs_modulus": None,
                    "density": None,
                    "d10": None,
                    "d50": None,
                    "d90": None,
                    "process_duration": None,
                }

                # Attempt to extract density from thermo if available
                if record["thermo"]:
                    density_val = record["thermo"].get("density")
                    if density_val is not None:
                        record["density"] = float(density_val)

                batch_records.append(record)

            all_records.extend(batch_records)
            total_fetched += len(batch_records)
            logger.info(f"Page {page}: Fetched {len(batch_records)} records (Total: {total_fetched})")

            # Exponential backoff to respect rate limits
            time.sleep(0.5)

        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed on page {page}: {e}")
            # If we have some data, return what we have; otherwise skip source
            if all_records:
                logger.warning("Partial success: returning fetched data despite error.")
                break
            else:
                logger.warning("Source skipped: Materials Project (no rows or error)")
                return []

    if total_fetched == 0:
        logger.warning("Source skipped: Materials Project (no rows or error)")
        return []

    logger.info(f"Fetch complete. Total: {total_fetched}, Filtered: {total_filtered}")
    return all_records

def save_to_json(data: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Saves the fetched data to a JSON file.

    Args:
        data: List of records to save.
        output_path: Path to the output JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)
    logger.info(f"Data saved to {output_path}")

def run_materials_project_ingestion() -> List[Dict[str, Any]]:
    """
    Main entry point for the Materials Project ingestion task (T012).

    Returns:
        List of fetched records.
    """
    records = fetch_materials_project_data()

    if records:
        # Validate traceability before saving
        valid_records = []
        for r in records:
            if r.get("source_id"):
                valid_records.append(r)
            else:
                logger.warning(f"Row filtered: missing traceability metadata (source_id)")

        if valid_records:
            save_to_json(valid_records, OUTPUT_PATH)
            return valid_records
        else:
            logger.warning("All records filtered due to missing source_id.")
            return []
    else:
        # Ensure output file is not created if no data (or create empty if required by pipeline)
        # Per task: "Output: data/raw/materials_project_raw.json"
        # We create an empty file to indicate the source was processed but yielded nothing.
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT_PATH.write_text("[]", encoding="utf-8")
        logger.info("Created empty output file (no data fetched).")
        return []

if __name__ == "__main__":
    run_materials_project_ingestion()
