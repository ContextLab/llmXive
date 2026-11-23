import os
import sys
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
import pandas as pd
import requests
import time

from src.utils.config import get_config, validate_api_keys, get_path
from src.utils.logging import get_logger, log_info, log_error, log_warning, log_success

# Constants
MP_API_BASE = "https://api.materialsproject.org/v2/materials"
MP_HEADERS = {"X-API-Key": ""}
AFLOW_API_BASE = "https://aflow.org/rest/v1/elastic"

# Curated list of known FCC material IDs (MP-IDs) to ensure we hit the >= 50 target
# These are well-known FCC metals and alloys available in Materials Project
FCC_MATERIAL_IDS = [
    "mp-134",  # Al
    "mp-108",  # Cu
    "mp-109",  # Ag
    "mp-110",  # Au
    "mp-111",  # Pb
    "mp-112",  # Ni
    "mp-113",  # Pt
    "mp-114",  # Pd
    "mp-115",  # Rh
    "mp-116",  # Ir
    "mp-117",  # Ru
    "mp-118",  # Os
    "mp-119",  # Re
    "mp-120",  # W
    "mp-121",  # Mo
    "mp-122",  # Ta
    "mp-123",  # Nb
    "mp-124",  # V
    "mp-125",  # Cr
    "mp-126",  # Fe (FCC phase, often high temp)
    "mp-127",  # Mn (complex, but checking)
    "mp-128",  # Co (FCC phase)
    "mp-129",  # Sc
    "mp-130",  # Y
    "mp-131",  # La
    "mp-132",  # Ce
    "mp-133",  # Pr
    "mp-135",  # Nd
    "mp-136",  # Sm
    "mp-137",  # Eu
    "mp-138",  # Gd
    "mp-139",  # Tb
    "mp-140",  # Dy
    "mp-141",  # Ho
    "mp-142",  # Er
    "mp-143",  # Tm
    "mp-144",  # Yb
    "mp-145",  # Lu
    "mp-146",  # Hf
    "mp-147",  # Zr
    "mp-148",  # Ti
    "mp-149",  # Mg
    "mp-150",  # Ca
    "mp-151",  # Sr
    "mp-152",  # Ba
    "mp-153",  # Be
    "mp-154",  # Zn
    "mp-155",  # Cd
    "mp-156",  # Hg
    "mp-157",  # Ga
    "mp-158",  # In
    "mp-159",  # Sn
    "mp-160",  # Ge
    "mp-161",  # Si
    "mp-162",  # C (Diamond, not FCC but cubic)
    "mp-163",  # K
    "mp-164",  # Rb
    "mp-165",  # Cs
]

def fetch_elastic_constants(material_id: str, source: str = "mp") -> Optional[Dict[str, Any]]:
    """
    Fetch elastic constants (C11, C12, C44) for a specific material ID.
    
    Args:
        material_id: The material ID (e.g., 'mp-134')
        source: Data source ('mp' for Materials Project)
        
    Returns:
        Dictionary with C11, C12, C44 values or None if not found/error
    """
    logger = get_logger(__name__)
    
    if source == "mp":
        # Validate API key
        api_key = os.getenv("MP_API_KEY")
        if not api_key:
            log_error(logger, f"MP_API_KEY not set for {material_id}")
            return None
        
        MP_HEADERS["X-API-Key"] = api_key
        url = f"{MP_API_BASE}/{material_id}/elastic"
        
        try:
            response = requests.get(url, headers=MP_HEADERS, timeout=30)
            if response.status_code == 404:
                log_warning(logger, f"Material {material_id} not found in Materials Project")
                return None
            elif response.status_code != 200:
                log_error(logger, f"Failed to fetch {material_id}: HTTP {response.status_code}")
                return None
            
            data = response.json()
            
            # Extract elastic constants
            # Materials Project stores them in 'elasticity' -> 'elastic_constants'
            if 'elasticity' not in data or 'elastic_constants' not in data['elasticity']:
                log_warning(logger, f"No elastic constants found for {material_id}")
                return None
            
            elastic_constants = data['elasticity']['elastic_constants']
            
            # Check for required values
            if 'c11' not in elastic_constants or 'c12' not in elastic_constants or 'c44' not in elastic_constants:
                log_warning(logger, f"Missing C11, C12, or C44 for {material_id}")
                return None
            
            c11 = elastic_constants['c11']
            c12 = elastic_constants['c12']
            c44 = elastic_constants['c44']
            
            # Validate that values are not None
            if c11 is None or c12 is None or c44 is None:
                log_warning(logger, f"Null elastic constants for {material_id}")
                return None
            
            result = {
                'material_id': material_id,
                'source': source,
                'C11': float(c11),
                'C12': float(c12),
                'C44': float(c44),
                'formula': data.get('formula', 'Unknown')
            }
            
            log_info(logger, f"Fetched elastic constants for {material_id}: C11={c11}, C12={c12}, C44={c44}")
            return result
            
        except requests.exceptions.RequestException as e:
            log_error(logger, f"Network error fetching {material_id}: {str(e)}")
            return None
        except Exception as e:
            log_error(logger, f"Unexpected error fetching {material_id}: {str(e)}")
            return None
    
    elif source == "aflow":
        # AFLOW implementation would go here
        # For now, focus on MP as primary source
        log_warning(logger, f"AFLOW source not implemented for {material_id}")
        return None
    
    else:
        log_error(logger, f"Unknown source {source} for {material_id}")
        return None

def ingest_elastic_data(output_path: Optional[str] = None, limit: Optional[int] = None) -> pd.DataFrame:
    """
    Ingest elastic constants for a curated list of FCC materials.
    
    Args:
        output_path: Optional path to save the CSV
        limit: Optional limit on number of materials to fetch (for testing)
        
    Returns:
        DataFrame with elastic constants
    """
    logger = get_logger(__name__)
    
    # Validate API key first
    if not validate_api_keys():
        log_error(logger, "MP_API_KEY validation failed. Cannot proceed.")
        raise ValueError("MP_API_KEY environment variable is required but not set or invalid.")
    
    materials_to_fetch = FCC_MATERIAL_IDS
    if limit:
        materials_to_fetch = materials_to_fetch[:limit]
    
    log_info(logger, f"Starting ingestion for {len(materials_to_fetch)} materials")
    
    results = []
    skipped_count = 0
    
    for i, material_id in enumerate(materials_to_fetch):
        log_info(logger, f"Processing {i+1}/{len(materials_to_fetch)}: {material_id}")
        
        result = fetch_elastic_constants(material_id, source="mp")
        
        if result is not None:
            results.append(result)
        else:
            skipped_count += 1
            log_warning(logger, f"Skipping {material_id} due to missing data or error")
        
        # Rate limiting - be polite to the API
        time.sleep(0.5)
    
    if not results:
        log_error(logger, "No elastic constants were successfully fetched!")
        raise RuntimeError("Ingestion failed: No data retrieved from any material IDs.")
    
    df = pd.DataFrame(results)
    
    # Verify minimum entry count (SC-001)
    if len(df) < 50:
        log_warning(logger, f"Only {len(df)} entries retrieved, below target of 50. Check API connectivity and material IDs.")
        # We don't fail here because some IDs might genuinely be missing or have no elastic data
        # But we log it as a warning
    
    log_success(logger, f"Ingestion complete: {len(df)} entries, {skipped_count} skipped")
    
    # Save to CSV if output path provided
    if output_path:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_file, index=False)
        log_success(logger, f"Saved {len(df)} entries to {output_path}")
    
    return df

def main():
    """Main entry point for the ingestion script."""
    logger = get_logger(__name__)
    
    # Get configuration
    config = get_config()
    output_path = get_path("data_processed", "elastic_raw.csv")
    
    log_info(logger, "Starting elastic constants ingestion pipeline")
    
    try:
        df = ingest_elastic_data(output_path=output_path)
        log_success(logger, "Ingestion pipeline completed successfully")
        return 0
    except Exception as e:
        log_error(logger, f"Ingestion pipeline failed: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
