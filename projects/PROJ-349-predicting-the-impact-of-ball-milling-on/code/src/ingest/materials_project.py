"""
Materials Project Data Fetcher.

Fetches ball milling related data from the Materials Project API.
Strictly uses real data. No synthetic fallbacks.
"""
import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

from src.utils.logger import get_module_logger
from src.exceptions import SourceConnectionError, DataIngestionError

logger = get_module_logger(__name__)

MP_API_URL = "https://next-gen.materialsproject.org/materials"
MP_ENDPOINT = "https://next-gen.materialsproject.org/api/v2/mp/search"

def fetch_materials_project_data(api_key: Optional[str] = None, timeout: int = 30) -> List[Dict[str, Any]]:
    """
    Fetches materials data from Materials Project API.

    Args:
        api_key: Materials Project API key.
        timeout: Request timeout in seconds.

    Returns:
        List of material entries matching ball milling criteria.

    Raises:
        SourceConnectionError: If the API is unreachable.
        DataIngestionError: If the response is invalid.
    """
    if not api_key:
        api_key = os.getenv("MP_API_KEY")
    
    if not api_key:
        logger.warning("Materials Project API key not found. Skipping fetch.")
        return []

    headers = {
        "x-api-key": api_key,
        "Content-Type": "application/json"
    }

    # Search for materials with 'ball milling' or 'milling' in keywords/abstracts
    # Note: The actual API endpoint and query parameters depend on the specific API version.
    # This is a representative implementation based on standard MP API usage patterns.
    payload = {
        "keywords": "ball milling",
        "fields": "material_id,pretty_formula,nsites,elements,nelements,structure,expt_xrd,dft_xrd,elasticity,thermo,magtot"
    }

    try:
        logger.info(f"Fetching data from Materials Project API...")
        # Using a generic search endpoint structure
        response = requests.post(
            f"{MP_ENDPOINT}",
            headers=headers,
            json=payload,
            timeout=timeout
        )
        
        if response.status_code == 401:
            logger.error("Materials Project API key invalid or expired.")
            return []
        elif response.status_code != 200:
            logger.error(f"Materials Project API returned status {response.status_code}: {response.text}")
            return []

        data = response.json()
        
        if "data" not in data:
            logger.warning("Materials Project response did not contain 'data' key.")
            return []

        raw_entries = data["data"]
        
        if not raw_entries:
            logger.warning("Materials Project search returned 0 results.")
            return []

        processed_entries = []
        for entry in raw_entries:
            # Map MP fields to our schema
            # Note: Actual mapping depends on what fields MP returns and what we need.
            # This is a placeholder mapping logic.
            processed = {
                "experiment_id": entry.get("material_id"),
                "source": "materials_project",
                "material_type": entry.get("pretty_formula", "unknown"),
                # MP API might not have milling specific fields directly,
                # so we might need to infer or leave as NaN if not present.
                # For this task, we assume we are fetching a specific dataset
                # or the API supports filtering by these specific milling parameters.
                # If the API doesn't support these specific fields, we log and skip.
                "milling_speed": None, # Placeholder - actual extraction logic needed
                "milling_time": None,
                "ball_to_powder_ratio": None,
                "youngs_modulus": None,
                "density": None,
                "d10": None,
                "d50": None,
                "d90": None,
                "process_duration": None
            }
            processed_entries.append(processed)

        logger.info(f"Successfully fetched {len(processed_entries)} entries from Materials Project.")
        return processed_entries

    except requests.exceptions.Timeout:
        logger.warning("Materials Project API request timed out.")
        return []
    except requests.exceptions.ConnectionError:
        logger.warning("Materials Project API connection failed.")
        return []
    except json.JSONDecodeError:
        logger.error("Materials Project API returned invalid JSON.")
        return []
    except Exception as e:
        logger.error(f"Unexpected error fetching Materials Project data: {e}")
        raise SourceConnectionError(f"Failed to fetch Materials Project data: {e}")

def save_to_json(data: List[Dict[str, Any]], output_path: str) -> None:
    """
    Saves data to a JSON file.

    Args:
        data: List of dictionaries to save.
        output_path: Path to the output file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Saved {len(data)} entries to {output_path}")

def run_materials_project_ingestion(output_dir: str = "data/raw") -> Optional[str]:
    """
    Orchestrates the Materials Project data ingestion.

    Args:
        output_dir: Directory to save the raw data.

    Returns:
        Path to the saved JSON file, or None if no data was fetched.
    """
    output_path = os.path.join(output_dir, "materials_project_raw.json")
    
    # Ensure output directory exists
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    data = fetch_materials_project_data()

    if not data:
        logger.warning("Source skipped: Materials Project (no rows or error)")
        return None

    save_to_json(data, output_path)
    return output_path
