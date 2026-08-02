import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import requests

from src.utils.config import get_data_path
from src.utils.logger import get_logger
from src.data.traits_cache import cache_raw_response

# Initialize logger
logger = get_logger(__name__)

def load_target_species_list() -> List[Dict[str, Any]]:
    """
    Load target species list from the post-QC species list file.
    
    Returns:
        List of species dictionaries with 'species' key.
    """
    input_path = get_data_path() / "processed" / "post_qc_species_list.json"
    
    if not input_path.exists():
        raise FileNotFoundError(
            f"Target species list not found at {input_path}. "
            "Ensure T014 (QC logic) has been executed."
        )
    
    with open(input_path, 'r') as f:
        data = json.load(f)
    
    # Handle both list format and dict format
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'species' in data:
        return data['species']
    else:
        raise ValueError(f"Unexpected format in {input_path}")

def fetch_traits_for_species(
    species_name: str, 
    api_key: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Fetch defense trait data for a single species from the TRY database.
    
    Args:
        species_name: Scientific name of the species.
        api_key: TRY API key (if available).
        
    Returns:
        Dictionary of trait data if found, None otherwise.
    """
    if not api_key:
        logger.warning(f"TRY_API_KEY not set, skipping fetch for {species_name}")
        return None
    
    # TRY Database API endpoint (example - adjust based on actual API)
    # Note: The TRY database API structure may vary; this is a placeholder
    # for the actual implementation based on the real API documentation.
    base_url = "https://try-db.org/api/v1/species"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json"
    }
    
    params = {
        "scientific_name": species_name,
        "trait_ids": "1,2,3,4,5"  # Example trait IDs for defense traits
    }
    
    try:
        response = requests.get(
            base_url, 
            headers=headers, 
            params=params, 
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            # Cache the raw response
            cache_raw_response("try", species_name, data)
            return data
        elif response.status_code == 404:
            logger.info(f"Species {species_name} not found in TRY database")
            return None
        else:
            logger.error(f"TRY API error for {species_name}: {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error fetching traits for {species_name}: {str(e)}")
        return None

def compile_try_results(
    target_species: List[Dict[str, Any]], 
    try_results: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Compile TRY database results into the summary format.
    
    Args:
        target_species: List of target species.
        try_results: Dictionary mapping species names to trait data.
        
    Returns:
        Compiled results dictionary.
    """
    missing_from_try = []
    
    for species_entry in target_species:
        species_name = species_entry.get('species', species_entry)
        
        if species_name in try_results and try_results[species_name] is not None:
            # Successfully fetched
            pass
        else:
            missing_from_try.append(species_name)
    
    return {
        "target_species": [s.get('species', s) if isinstance(s, dict) else s for s in target_species],
        "primary_source_results": {
            sp: tr for sp, tr in try_results.items() 
            if tr is not None
        },
        "missing_from_try": missing_from_try,
        "missing_from_all_sources": []  # Will be updated by fallback task
    }

def save_trait_fallback_summary(
    summary_data: Dict[str, Any], 
    api_key_status: str = "present"
) -> None:
    """
    Save the trait fallback summary to the output file.
    
    Args:
        summary_data: The compiled summary data.
        api_key_status: Status of the API key ("present" or "missing").
    """
    output_path = get_data_path() / "processed" / "trait_fallback_summary.json"
    
    # Add API key status
    summary_data["try_api_key_status"] = api_key_status
    
    with open(output_path, 'w') as f:
        json.dump(summary_data, f, indent=2)
    
    logger.info(f"Saved trait fallback summary to {output_path}")

def main() -> None:
    """
    Main function to fetch defense trait data from TRY database.
    
    This function:
    1. Loads target species from post-QC list.
    2. Checks for TRY_API_KEY.
    3. Fetches traits for each species (if API key available).
    4. Compiles results and saves summary.
    5. Does NOT raise SystemExit if API key is missing (proceeds to fallback).
    """
    logger.info("Starting TRY database trait fetch (T025a)")
    
    # Load target species
    try:
        target_species = load_target_species_list()
        logger.info(f"Loaded {len(target_species)} target species")
    except FileNotFoundError as e:
        logger.error(str(e))
        # Create an empty summary to allow pipeline to continue
        summary = {
            "target_species": [],
            "primary_source_results": {},
            "missing_from_try": [],
            "missing_from_all_sources": [],
            "try_api_key_status": "missing"
        }
        save_trait_fallback_summary(summary, "missing")
        return
    
    # Check for API key
    api_key = os.getenv("TRY_API_KEY")
    api_key_status = "present" if api_key else "missing"
    
    if not api_key:
        logger.warning("TRY_API_KEY environment variable is not set")
        logger.info("Proceeding without TRY data (will rely on fallback sources)")
    
    # Fetch traits for each species
    try_results = {}
    if api_key:
        for species_entry in target_species:
            species_name = species_entry.get('species', species_entry)
            logger.info(f"Fetching traits for {species_name}...")
            traits = fetch_traits_for_species(species_name, api_key)
            try_results[species_name] = traits
    else:
        # If no API key, all species are "missing"
        for species_entry in target_species:
            species_name = species_entry.get('species', species_entry)
            try_results[species_name] = None
    
    # Compile results
    summary = compile_try_results(target_species, try_results)
    
    # Save summary
    save_trait_fallback_summary(summary, api_key_status)
    
    logger.info(f"T025a completed. Missing from TRY: {len(summary['missing_from_try'])} species")

if __name__ == "__main__":
    main()
