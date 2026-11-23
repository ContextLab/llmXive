"""
Ingest data from Materials Project API (v3).

This script fetches composition data, phase information, and elemental properties
from the Materials Project API. It handles API failures gracefully by logging
warnings and proceeding with available data rather than halting execution.

Output: data/raw/materials_project_raw.csv
"""

import os
import sys
import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import requests
import pandas as pd

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utils.config import (
    get_materials_project_api_key,
    get_materials_project_base_url,
    get_raw_data_path,
    ensure_data_directories
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Materials Project API v3 endpoints
MP_COMPOSITIONS_ENDPOINT = "/materials"
MP_ELEMENTS_ENDPOINT = "/elements"

# Fields to fetch from Materials Project
MP_COMPOSITION_FIELDS = [
    "material_id",
    "formula_pretty",
    "formula_anonymous",
    "nelements",
    "nsites",
    "structure",
    "energy_per_atom",
    "formation_energy_per_atom",
    "band_gap",
    "is_metal",
    "is_gap_direct",
    "is_stable",
    "decomposes_to",
    "thermodynamic_data",
    "cif"
]

MP_ELEMENT_FIELDS = [
    "element",
    "atomic_number",
    "atomic_mass",
    "atomic_radius",
    "atomic_radius_chem",
    "electronegativity",
    "melting_point",
    "boiling_point",
    "density",
    "molar_volume",
    "thermal_conductivity",
    "electrical_resistivity",
    "specific_heat",
    "heat_fusion",
    "heat_vaporization",
    "coefficient_thermal_expansion",
    "bulk_modulus",
    "shear_modulus",
    "youngs_modulus",
    "poisson_ratio",
    "magnetization_per_formula_unit",
    "total_magnetic_moment",
    "formation_energy_per_atom",
    "energy_per_atom",
    "number_of_electrons",
    "number_of_protons",
    "number_of_neutrons",
    "number_of_orbitals",
    "number_of_valence_electrons",
    "group",
    "period",
    "block",
    "electron_configuration",
    "electron_affinity",
    "ionization_energies",
    "dft_correction"
]

# Default phase labels based on Materials Project data
DEFAULT_PHASE_LABELS = {
    "is_metal": "crystalline",
    "is_stable": "stable",
    "decomposes_to": None
}

def fetch_materials_project_compositions(
    api_key: str,
    base_url: str,
    limit: Optional[int] = None,
    batch_size: int = 100
) -> List[Dict[str, Any]]:
    """
    Fetch composition data from Materials Project API.
    
    Args:
        api_key: Materials Project API key
        base_url: Base URL for Materials Project API
        limit: Maximum number of records to fetch (None for all)
        batch_size: Number of records per request
        
    Returns:
        List of composition records
    """
    compositions = []
    url = f"{base_url}{MP_COMPOSITIONS_ENDPOINT}"
    params = {
        "api_key": api_key,
        "fields": ",".join(MP_COMPOSITION_FIELDS),
        "limit": batch_size,
        "offset": 0
    }
    
    total_fetched = 0
    max_retries = 3
    retry_delay = 5  # seconds
    
    logger.info(f"Fetching Materials Project compositions from {url}")
    
    while True:
        try:
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                if not data or "data" not in data or len(data["data"]) == 0:
                    logger.info("No more data available from Materials Project")
                    break
                
                # Extract records
                records = data["data"]
                compositions.extend(records)
                total_fetched += len(records)
                
                logger.info(f"Fetched {len(records)} records (total: {total_fetched})")
                
                # Check if we've reached the limit
                if limit and total_fetched >= limit:
                    logger.info(f"Reached limit of {limit} records")
                    break
                
                # Prepare next request
                params["offset"] += batch_size
                
                # Small delay to avoid rate limiting
                if len(records) < batch_size:
                    break
                
            elif response.status_code == 401:
                logger.error("Authentication failed. Check API key.")
                raise ValueError("Invalid Materials Project API key")
            elif response.status_code == 404:
                logger.error(f"Endpoint not found: {url}")
                raise ValueError(f"Materials Project endpoint not found: {url}")
            elif response.status_code == 429:
                logger.warning("Rate limit exceeded. Waiting before retry...")
                time.sleep(retry_delay)
                retry_delay *= 2
                continue
            else:
                logger.error(f"API returned status code: {response.status_code}")
                logger.error(f"Response: {response.text[:200]}")
                # Don't halt on API errors, just log and stop fetching
                break
                
        except requests.exceptions.Timeout:
            logger.warning("Request timed out. Stopping fetch.")
            break
        except requests.exceptions.ConnectionError as e:
            logger.warning(f"Connection error: {str(e)}. Stopping fetch.")
            break
        except requests.exceptions.RequestException as e:
            logger.warning(f"Request error: {str(e)}. Stopping fetch.")
            break
        except Exception as e:
            logger.warning(f"Unexpected error during fetch: {str(e)}. Stopping fetch.")
            break
    
    logger.info(f"Total compositions fetched: {len(compositions)}")
    return compositions

def fetch_materials_project_elements(
    api_key: str,
    base_url: str
) -> Dict[str, Dict[str, Any]]:
    """
    Fetch elemental properties from Materials Project API.
    
    Args:
        api_key: Materials Project API key
        base_url: Base URL for Materials Project API
        
    Returns:
        Dictionary mapping element symbols to their properties
    """
    url = f"{base_url}{MP_ELEMENTS_ENDPOINT}"
    params = {
        "api_key": api_key,
        "fields": ",".join(MP_ELEMENT_FIELDS)
    }
    
    elements = {}
    
    try:
        logger.info(f"Fetching Materials Project elements from {url}")
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            if data and "data" in data:
                for elem_data in data["data"]:
                    element_symbol = elem_data.get("element")
                    if element_symbol:
                        elements[element_symbol] = elem_data
                
                logger.info(f"Fetched properties for {len(elements)} elements")
            else:
                logger.warning("No element data returned from API")
        else:
            logger.warning(f"Failed to fetch elements: {response.status_code}")
            
    except Exception as e:
        logger.warning(f"Error fetching element properties: {str(e)}")
    
    return elements

def process_mp_data(
    compositions: List[Dict[str, Any]],
    element_properties: Dict[str, Dict[str, Any]]
) -> pd.DataFrame:
    """
    Process Materials Project data into a structured DataFrame.
    
    Args:
        compositions: List of composition records from API
        element_properties: Dictionary of elemental properties
        
    Returns:
        Processed DataFrame with composition data and elemental properties
    """
    records = []
    
    for comp in compositions:
        record = {
            "material_id": comp.get("material_id"),
            "composition": comp.get("formula_pretty"),
            "formula_anonymous": comp.get("formula_anonymous"),
            "nelements": comp.get("nelements"),
            "nsites": comp.get("nsites"),
            "energy_per_atom": comp.get("energy_per_atom"),
            "formation_energy_per_atom": comp.get("formation_energy_per_atom"),
            "band_gap": comp.get("band_gap"),
            "is_metal": comp.get("is_metal"),
            "is_gap_direct": comp.get("is_gap_direct"),
            "is_stable": comp.get("is_stable"),
            "decomposes_to": comp.get("decomposes_to"),
            "source": "Materials Project"
        }
        
        # Derive phase label from Materials Project fields
        if comp.get("is_metal") is True:
            record["phase"] = "crystalline"
        elif comp.get("is_stable") is True:
            record["phase"] = "stable_crystalline"
        elif comp.get("decomposes_to") is not None:
            record["phase"] = "unstable"
        else:
            record["phase"] = "unknown"
        
        # Store elemental properties for each element in the composition
        # This will be used later for feature engineering
        elements_in_comp = {}
        formula = comp.get("formula_pretty", "")
        
        # Parse formula to get elements and their counts
        # Simple parsing: split by element symbols (capital letter followed by optional lowercase)
        import re
        pattern = r'([A-Z][a-z]?)(\d*)'
        matches = re.findall(pattern, formula)
        
        for element, count in matches:
            if count:
                count = int(count)
            else:
                count = 1
            elements_in_comp[element] = count
            
            # Add element-specific properties if available
            if element in element_properties:
                elem_props = element_properties[element]
                record[f"{element}_atomic_radius"] = elem_props.get("atomic_radius")
                record[f"{element}_electronegativity"] = elem_props.get("electronegativity")
                record[f"{element}_atomic_mass"] = elem_props.get("atomic_mass")
                record[f"{element}_valence_electrons"] = elem_props.get("number_of_valence_electrons")
        
        # Store the element composition as a JSON string for later processing
        record["element_composition"] = json.dumps(elements_in_comp)
        
        records.append(record)
    
    df = pd.DataFrame(records)
    logger.info(f"Processed {len(df)} records from Materials Project")
    return df

def main():
    """Main entry point for Materials Project data ingestion."""
    logger.info("Starting Materials Project data ingestion")
    
    # Ensure data directories exist
    ensure_data_directories()
    
    # Get configuration
    api_key = get_materials_project_api_key()
    base_url = get_materials_project_base_url()
    
    if not api_key:
        logger.warning("Materials Project API key not found in environment variables")
        logger.warning("Proceeding without API key - will attempt to fetch available data")
        # Continue without API key, the fetch function will handle this
    
    # Fetch compositions
    compositions = fetch_materials_project_compositions(
        api_key=api_key,
        base_url=base_url,
        limit=5000  # Limit to avoid excessive API calls
    )
    
    # If no compositions fetched, log warning but continue
    if not compositions:
        logger.warning("No compositions fetched from Materials Project API")
        logger.warning("Proceeding with empty dataset - downstream processes may need fallback data")
        # Create empty DataFrame with expected columns
        df = pd.DataFrame(columns=[
            "material_id", "composition", "formula_anonymous", "nelements",
            "nsites", "energy_per_atom", "formation_energy_per_atom",
            "band_gap", "is_metal", "is_gap_direct", "is_stable",
            "decomposes_to", "source", "phase", "element_composition"
        ])
    else:
        # Fetch elemental properties
        element_properties = fetch_materials_project_elements(api_key, base_url)
        
        # Process data
        df = process_mp_data(compositions, element_properties)
    
    # Save output
    output_path = get_raw_data_path() / "materials_project_raw.csv"
    df.to_csv(output_path, index=False)
    logger.info(f"Saved Materials Project data to {output_path}")
    logger.info(f"Total records: {len(df)}")
    
    # Log summary statistics
    if len(df) > 0:
        logger.info(f"Phase distribution:\n{df['phase'].value_counts()}")
        logger.info(f"Metallic compounds: {df['is_metal'].sum()}")
        logger.info(f"Stable compounds: {df['is_stable'].sum()}")
    
    return df

if __name__ == "__main__":
    main()
