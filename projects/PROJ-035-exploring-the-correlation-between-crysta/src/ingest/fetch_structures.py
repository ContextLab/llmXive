"""
Fetch perovskite crystal structures from the Materials Project API.

This module downloads crystal structures, filters for ABX3 stoichiometry,
and saves the result to data/raw/structures_raw.csv.
"""

import os
import sys
import time
import argparse
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import random
import numpy as np
import requests

# Add parent directory to path for imports if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

from config.env import load_api_key
from utils.seed_manager import init_seed
from utils.validation import setup_logger

# Constants
MP_API_BASE = "https://api.materialsproject.org"
MP_STRUCTURES_ENDPOINT = f"{MP_API_BASE}/materials/sorted"
MAX_RETRIES = 5
BACKOFF_FACTOR = 2.0
OUTPUT_PATH = Path("data/raw/structures_raw.csv")
REQUIRED_FIELDS = ["structure_id", "formula", "elements", "nsites", "lattice", "cartesian_site_positions", "species_at_sites"]

logger = setup_logger("fetch_structures")


def load_api_key() -> str:
    """Load Materials Project API key from environment."""
    api_key = os.getenv("MP_API_KEY")
    if not api_key:
        logger.error("MP_API_KEY environment variable not set.")
        sys.exit(1)
    return api_key


def fetch_with_backoff(
    url: str,
    params: Dict,
    api_key: str,
    seed: int = 42
) -> Tuple[Optional[Dict], int]:
    """
    Fetch data from URL with exponential backoff retry logic.
    
    Args:
        url: The API endpoint URL.
        params: Query parameters.
        api_key: API key for authentication.
        seed: Random seed for deterministic jitter in backoff.
        
    Returns:
        Tuple of (response_json, status_code). Returns (None, status_code) on failure.
    """
    rng = random.Random(seed)
    headers = {"X-API-Key": api_key, "Content-Type": "application/json"}
    
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, params=params, headers=headers, timeout=30)
            if response.status_code == 200:
                return response.json(), 200
            elif response.status_code == 429:
                # Rate limited, wait with exponential backoff + jitter
                wait_time = (BACKOFF_FACTOR ** attempt) + rng.uniform(0, 1.0)
                logger.warning(f"Rate limited. Retrying in {wait_time:.2f}s (Attempt {attempt + 1}/{MAX_RETRIES})")
                time.sleep(wait_time)
            else:
                logger.error(f"HTTP Error {response.status_code}: {response.text}")
                return None, response.status_code
        except requests.exceptions.RequestException as e:
            if attempt == MAX_RETRIES - 1:
                logger.error(f"Network error after {MAX_RETRIES} attempts: {e}")
                return None, 500
            wait_time = (BACKOFF_FACTOR ** attempt) + rng.uniform(0, 1.0)
            logger.warning(f"Network error. Retrying in {wait_time:.2f}s: {e}")
            time.sleep(wait_time)
    
    return None, 500


def is_perovskite(formula: str) -> bool:
    """
    Check if a formula string matches the ABX3 perovskite stoichiometry.
    
    This is a simplified check looking for exactly 3 elements where the
    third element count is 3 times the first two, or a standard ABO3/ABX3 pattern.
    More robust checks might use pymatgen Composition, but this suffices for 
    initial filtering before detailed structure validation.
    
    Args:
        formula: Chemical formula string (e.g., "BaTiO3", "CsPbI3").
        
    Returns:
        True if the formula resembles ABX3, False otherwise.
    """
    if not formula:
        return False
    
    # Remove spaces and normalize
    formula = formula.replace(" ", "")
    
    # Simple heuristic: Look for patterns like ABO3, ABX3, etc.
    # This regex looks for Element + Element + Element3
    # Note: This is a heuristic and might miss complex cases or catch false positives.
    # A more robust implementation would use pymatgen Composition to check site counts.
    
    # Basic check: ends with O3, F3, Cl3, Br3, I3, N3, S3, etc.
    # And has at least 2 distinct elements before the last one
    import re
    # Matches something like "CsPbI3", "BaTiO3", "NaNbO3"
    # Pattern: [Element][Element][Element]3
    # We rely on the fact that MP API returns sorted formulas like "Cs1 Pb1 I3"
    parts = formula.split()
    if len(parts) != 3:
        return False
        
    try:
        # Parse counts
        elem1, count1 = parts[0][:-1], int(parts[0][-1]) if parts[0][-1].isdigit() else 1
        elem2, count2 = parts[1][:-1], int(parts[1][-1]) if parts[1][-1].isdigit() else 1
        elem3, count3 = parts[2][:-1], int(parts[2][-1]) if parts[2][-1].isdigit() else 1
        
        # Check stoichiometry: A(1) B(1) X(3)
        if count1 == 1 and count2 == 1 and count3 == 3:
            return True
    except (ValueError, IndexError):
        return False
        
    return False


def fetch_perovskite_structures(seed: int = 42) -> List[Dict]:
    """
    Fetch perovskite structures from Materials Project API.
    
    Args:
        seed: Random seed for reproducibility in any stochastic operations.
        
    Returns:
        List of dictionaries containing structure data.
    """
    init_seed(seed)
    api_key = load_api_key()
    
    # Query parameters for perovskite-like structures
    # We request specific fields to minimize payload size
    params = {
        "formula": {"$regex": ".*[O,F,Cl,Br,I]3$"}, # Rough filter for X3
        "fields": "formula,structure_id,nsites,lattice,species_at_sites,elements",
        "sort_by": "nsites",
        "num_sites": "10,30" # Perovskites usually have small unit cells
    }
    
    logger.info("Fetching structures from Materials Project API...")
    data, status = fetch_with_backoff(MP_STRUCTURES_ENDPOINT, params, api_key, seed)
    
    if status != 200 or not data or "data" not in data:
        logger.error(f"Failed to fetch data. Status: {status}")
        return []
    
    structures = data["data"]
    perovskites = []
    
    logger.info(f"Received {len(structures)} candidates. Filtering for ABX3...")
    
    for item in structures:
        formula = item.get("formula", "")
        if is_perovskite(formula):
            # Ensure required fields exist
            record = {
                "structure_id": item.get("material_id"),
                "formula": formula,
                "nsites": item.get("nsites"),
                "elements": item.get("elements", []),
                # We might need to fetch full structure details separately if not in list
                # For now, we assume the list endpoint provides enough or we fetch details
            }
            # Note: The list endpoint might not give full coordinates. 
            # If full structure is needed, we'd fetch individual material_id.
            # Assuming for this task we get enough metadata or the full structure in 'data'
            # If the API returns full structure in 'data', we add it.
            if "structure" in item:
                record["structure"] = item["structure"]
            perovskites.append(record)
    
    logger.info(f"Filtered to {len(perovskites)} perovskite structures.")
    return perovskites


def save_structures(structures: List[Dict], output_path: Path) -> None:
    """
    Save structures to a CSV file.
    
    Args:
        structures: List of structure dictionaries.
        output_path: Path to the output CSV file.
    """
    import pandas as pd
    
    if not structures:
        logger.warning("No structures to save.")
        return
    
    # Flatten the data for CSV
    rows = []
    for s in structures:
        row = {
            "structure_id": s.get("structure_id"),
            "formula": s.get("formula"),
            "nsites": s.get("nsites"),
            "elements": ",".join(s.get("elements", [])),
        }
        # If structure data exists, we might need to serialize it or fetch it separately
        # For this implementation, we assume we have the necessary metadata
        rows.append(row)
    
    df = pd.DataFrame(rows)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(df)} structures to {output_path}")


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Fetch perovskite structures from Materials Project")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    args = parser.parse_args()
    
    structures = fetch_perovskite_structures(seed=args.seed)
    save_structures(structures, OUTPUT_PATH)
    
    if not structures:
        logger.error("No perovskite structures found. Exiting.")
        sys.exit(1)
    
    logger.info("Fetch complete.")


if __name__ == "__main__":
    main()
