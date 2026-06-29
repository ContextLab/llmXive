"""Fetch perovskite crystal structures from Materials Project API.

This module downloads crystal structure data from the Materials Project API,
filtering for ABX₃ stoichiometry (perovskites). Implements exponential backoff
retry logic (max 3 retries) and comprehensive error handling (FR-001).

Output: data/raw/structures.csv
"""

import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
import requests
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.validation import setup_logger, handle_error

# Configure logging
logger = setup_logger(__name__, level="INFO")

# Constants
MAX_RETRIES = 3
BASE_URL = "https://api.materialsproject.org"
OUTPUT_PATH = Path("data/raw/structures.csv")


def load_api_key() -> str:
    """Load Materials Project API key from environment.

    Returns:
        API key string

    Raises:
        ValueError: If API key is not configured
    """
    load_dotenv()
    api_key = os.getenv("MP_API_KEY")
    if not api_key:
        error_msg = "MP_API_KEY environment variable not set. " \
                   "Please configure your Materials Project API key."
        handle_error(error_msg, level="ERROR")
        raise ValueError(error_msg)
    return api_key


def fetch_with_backoff(
    url: str,
    headers: Dict,
    params: Optional[Dict] = None,
    max_retries: int = MAX_RETRIES
) -> Optional[Dict]:
    """Fetch data with exponential backoff retry logic.

    Args:
        url: API endpoint URL
        headers: Request headers
        params: Query parameters
        max_retries: Maximum retry attempts

    Returns:
        Response JSON or None if all retries fail
    """
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                handle_error(f"API request failed after {max_retries} retries: {e}", level="ERROR")
                return None
            wait_time = (2 ** attempt) * 5
            logger.warning(f"Retry {attempt + 1}/{max_retries} in {wait_time}s: {e}")
            time.sleep(wait_time)
    return None


def is_perovskite(formula: str) -> bool:
    """Check if formula matches ABX₃ perovskite stoichiometry.

    Args:
        formula: Chemical formula string

    Returns:
        True if formula matches ABX₃ pattern
    """
    parts = formula.replace(" ", "").split(":")
    if len(parts) != 3:
        return False

    try:
        ratios = [float(p) for p in parts]
        if min(ratios) == 0:
            return False
        min_ratio = min(ratios)
        normalized = [r / min_ratio for r in ratios]

        return (
            abs(normalized[0] - 1.0) < 0.01 and
            abs(normalized[1] - 1.0) < 0.01 and
            abs(normalized[2] - 3.0) < 0.01
        )
    except (ValueError, ZeroDivisionError):
        return False


def fetch_perovskite_structures(api_key: str) -> pd.DataFrame:
    """Fetch perovskite structures from Materials Project API.

    Args:
        api_key: Materials Project API key

    Returns:
        DataFrame with perovskite structure data
    """
    endpoint = f"{BASE_URL}/materials/docs"

    headers = {
        "X-API-Key": api_key,
        "Content-Type": "application/json"
    }

    params = {
        "limit": 1000,
        "criteria": {"formula_pretty": {"$regex": "^([A-Z][a-z]?[0-9]*:){2}[A-Z][a-z]?[0-9]*$"}},
        "fields": ["material_id", "formula_pretty", "nsites", "structure", "crystal_system", "space_group.number"]
    }

    logger.info("Fetching perovskite structures from Materials Project API...")
    response = fetch_with_backoff(endpoint, headers, params)

    if not response or "data" not in response:
        logger.warning("No data returned from API")
        return pd.DataFrame()

    materials = response["data"]
    logger.info(f"Retrieved {len(materials)} total materials")

    perovskite_structures = []
    for doc in materials:
        formula = doc.get("formula_pretty", "")
        if is_perovskite(formula):
            structure_data = {
                "structure_id": doc.get("material_id"),
                "formula": formula,
                "nsites": doc.get("nsites"),
                "crystal_system": doc.get("crystal_system"),
                "space_group": doc.get("space_group", {}).get("number")
            }
            perovskite_structures.append(structure_data)

    df = pd.DataFrame(perovskite_structures)
    logger.info(f"Filtered {len(df)} perovskite structures")
    return df


def main():
    """Main entry point for fetching perovskite structures."""
    try:
        api_key = load_api_key()
        structures_df = fetch_perovskite_structures(api_key)

        if structures_df.empty:
            logger.warning("No perovskite structures found")
            structures_df.to_csv(OUTPUT_PATH, index=False)
            return

        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        structures_df.to_csv(OUTPUT_PATH, index=False)
        logger.info(f"Saved {len(structures_df)} structures to {OUTPUT_PATH}")

    except ValueError as e:
        handle_error(str(e), level="ERROR")
        sys.exit(1)
    except Exception as e:
        handle_error(f"Unexpected error: {e}", level="ERROR")
        sys.exit(1)


if __name__ == "__main__":
    main()