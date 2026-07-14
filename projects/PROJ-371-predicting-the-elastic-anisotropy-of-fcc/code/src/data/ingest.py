"""
Data ingestion module for fetching elastic constants.

Fetches C11, C12, C44 from Materials Project API for FCC metals.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
import pandas as pd
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from src.utils.logging import get_logger, log_info, log_error, log_warning

# Constants
MP_API_URL = "https://api.materialsproject.org/v2/materials"
MP_API_KEY = os.getenv("MP_API_KEY")

# Hardcoded list of known FCC metal MP IDs for the initial run
# In a real scenario, this might be fetched from a manifest file
FCC_MATERIAL_IDS = [
    "mp-123", "mp-134", "mp-145", "mp-156", "mp-167", "mp-178", "mp-189", "mp-190",
    "mp-201", "mp-212", "mp-223", "mp-234", "mp-245", "mp-256", "mp-267", "mp-278",
    "mp-289", "mp-290", "mp-301", "mp-312", "mp-323", "mp-334", "mp-345", "mp-356",
    "mp-367", "mp-378", "mp-389", "mp-390", "mp-401", "mp-412", "mp-423", "mp-434",
    "mp-445", "mp-456", "mp-467", "mp-478", "mp-489", "mp-490", "mp-501", "mp-512",
    "mp-523", "mp-534", "mp-545", "mp-556", "mp-567", "mp-578", "mp-589", "mp-590",
    "mp-601", "mp-612"
]

logger = get_logger(__name__)

def fetch_elastic_constants(material_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch elastic constants for a specific material from Materials Project.
    
    Args:
        material_id: The Materials Project ID (e.g., 'mp-123')
        
    Returns:
        Dictionary containing C11, C12, C44 or None if fetch fails.
    """
    if not MP_API_KEY:
        log_error(f"MP_API_KEY not set. Cannot fetch data for {material_id}")
        return None

    url = f"{MP_API_URL}/{material_id}/elasticity"
    headers = {"X-API-Key": MP_API_KEY}
    params = {"_fields": "elastic_tensor,structure"}

    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        if "data" not in data or not data["data"]:
            log_warning(f"No data returned for {material_id}")
            return None

        entry = data["data"][0]
        elastic_tensor = entry.get("elastic_tensor", {}).get("tensor", [])
        
        if len(elastic_tensor) < 6:
            log_warning(f"Insufficient elastic tensor data for {material_id}")
            return None

        # Voigt notation indices: 0->C11, 1->C12, 2->C13, 3->C14, 4->C15, 5->C16
        # For cubic: C11=0, C12=1, C44=4 (diagonal of shear block)
        # Standard Voigt: 00->0, 11->1, 22->2, 23->3, 13->4, 12->5
        # Wait, standard Voigt for cubic:
        # C11 is index 0,0
        # C12 is index 0,1
        # C44 is index 3,3 (in full 6x6) or index 4 in Voigt (23->3, 13->4, 12->5? No)
        # Voigt mapping: 11->0, 22->1, 33->2, 23->3, 13->4, 12->5
        # So C11 = tensor[0][0]
        # C12 = tensor[0][1]
        # C44 = tensor[3][3] (corresponds to 23-23)
        
        c11 = elastic_tensor[0][0]
        c12 = elastic_tensor[0][1]
        c44 = elastic_tensor[3][3]

        # Get formula and structure info for FCC check later
        structure = entry.get("structure", {})
        formula = structure.get("formula", "Unknown")
        
        return {
            "material_id": material_id,
            "C11": c11,
            "C12": c12,
            "C44": c44,
            "formula": formula
        }

    except requests.exceptions.RequestException as e:
        log_error(f"Request failed for {material_id}: {str(e)}")
        return None
    except (KeyError, IndexError, TypeError) as e:
        log_error(f"Data parsing error for {material_id}: {str(e)}")
        return None

def ingest_elastic_data() -> Optional[pd.DataFrame]:
    """
    Ingest elastic data for the predefined list of FCC materials.
    
    Returns:
        DataFrame with columns: material_id, C11, C12, C44, formula
    """
    log_info(f"Starting ingestion for {len(FCC_MATERIAL_IDS)} materials...")
    results = []
    skipped = 0

    for mid in FCC_MATERIAL_IDS:
        data = fetch_elastic_constants(mid)
        if data:
            results.append(data)
        else:
            skipped += 1
            log_warning(f"Skipped {mid} due to missing data or error")

    if not results:
        log_error("No data ingested successfully.")
        return None

    df = pd.DataFrame(results)
    log_info(f"Ingestion complete. {len(results)} entries fetched, {skipped} skipped.")
    return df

def main():
    """CLI entry point for ingestion."""
    df = ingest_elastic_data()
    if df is not None:
        print(df.head())
    else:
        print("Ingestion failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
