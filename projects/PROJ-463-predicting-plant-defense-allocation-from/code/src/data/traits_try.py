"""
T025a: Fetch defense trait data from TRY database (Primary Source).

This module implements the primary data acquisition for plant defense traits
from the TRY database API. It reads the target species list from the QC output
and attempts to fetch trait data, logging failures for fallback processing.

Dependencies:
    - requests (for API calls)
    - os, sys, json, logging (standard library)

Environment Variables:
    - TRY_API_KEY: Required API key for authentication.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

try:
    import requests
except ImportError:
    print("ERROR: 'requests' library not found. Please install it via requirements.txt.")
    sys.exit(1)

# Import existing utilities from the project API surface
from src.utils.logger import get_logger
from src.utils.schemas import DefenseTrait, TraitDataset

# Configuration
TRY_API_BASE_URL = "https://www.try-db.org/TryWebAPI.php"
OUTPUT_FILE = Path("data/processed/trait_fallback_summary.json")
INPUT_FILE = Path("data/processed/post_qc_species_list.json")

# Logger setup
logger = get_logger(__name__)

def load_target_species_list() -> List[str]:
    """
    Reads the target species list from the QC output file.
    
    Returns:
        List[str]: List of species names.
        
    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If the file content is invalid.
    """
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Input file not found: {INPUT_FILE}")
    
    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # The schema from T014 is: { "species": <string>, "exclusion_reason": <string> }
        # But we need the list of species that PASSED QC. 
        # T014 output description says: "outputting a post-QC species list".
        # Assuming the file contains a list of valid species or a dict with a 'species' key if it's a list of passed items.
        # Based on T014 description: "outputting a post-QC species list to data/processed/post_qc_species_list.json"
        # Let's assume the structure is a list of species names or a list of objects where we extract 'species'.
        
        if isinstance(data, list):
            if len(data) == 0:
                logger.warning("Target species list is empty.")
                return []
            if isinstance(data[0], dict):
                return [item.get('species') for item in data if item.get('species')]
            return data
        elif isinstance(data, dict):
            if 'species' in data:
                return [data['species']]
            if 'valid_species' in data:
                return data['valid_species']
            raise ValueError(f"Unexpected JSON structure in {INPUT_FILE}: {data}")
        else:
            raise ValueError(f"Unexpected JSON type in {INPUT_FILE}: {type(data)}")
            
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {INPUT_FILE}: {e}")

def fetch_traits_for_species(species_name: str, api_key: str) -> Optional[Dict[str, Any]]:
    """
    Fetches defense trait data for a single species from the TRY database.
    
    Args:
        species_name: The scientific name of the species.
        api_key: The API key for authentication.
        
    Returns:
        Optional[Dict]: A dictionary containing trait data if successful, None otherwise.
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # TRY API payload structure (hypothetical based on common patterns, adjusted if spec differs)
    # The spec mentions "Use with species name and trait IDs".
    # We will attempt a general trait query for the species.
    payload = {
        "action": "getTraitData",
        "species": species_name,
        "trait_ids": []  # Empty list to fetch all available traits, or specific IDs if known
    }
    
    try:
        response = requests.post(
            TRY_API_BASE_URL,
            json=payload,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401:
            logger.error(f"Authentication failed for {species_name}. Check TRY_API_KEY.")
            return None
        elif response.status_code == 404:
            logger.warning(f"Species '{species_name}' not found in TRY database.")
            return None
        else:
            logger.error(f"TRY API error for {species_name}: {response.status_code} - {response.text}")
            return None
            
    except requests.exceptions.Timeout:
        logger.error(f"Timeout fetching data for {species_name}.")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed for {species_name}: {e}")
        return None

def compile_try_results(target_species: List[str], api_key: str) -> Dict[str, Any]:
    """
    Compiles the results of fetching traits for all target species.
    
    Args:
        target_species: List of species names to fetch.
        api_key: The API key for authentication.
        
    Returns:
        Dict[str, Any]: The summary dictionary matching the required schema.
    """
    primary_results = {}
    missing_species = []
    
    logger.info(f"Starting TRY fetch for {len(target_species)} species.")
    
    for species in target_species:
        logger.info(f"Fetching traits for: {species}")
        data = fetch_traits_for_species(species, api_key)
        
        if data:
            primary_results[species] = data
            logger.info(f"Successfully fetched traits for {species}.")
        else:
            missing_species.append(species)
            logger.warning(f"Failed to fetch traits for {species}. Adding to missing list.")
    
    return {
        "target_species": target_species,
        "primary_source_results": primary_results,
        "missing_from_try": missing_species,
        "fetched_at": datetime.utcnow().isoformat() + "Z"
    }

def save_trait_fallback_summary(summary_data: Dict[str, Any], output_path: Path) -> None:
    """
    Saves the compiled summary to the output JSON file.
    
    Args:
        summary_data: The summary dictionary.
        output_path: The path to the output file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(summary_data, f, indent=2, ensure_ascii=False)
    logger.info(f"Trait fallback summary saved to {output_path}")

def main() -> int:
    """
    Main entry point for T025a.
    
    Returns:
        int: 0 on success, 1 on failure.
    """
    # 1. Load API Key
    api_key = os.environ.get("TRY_API_KEY")
    if not api_key:
        logger.error("TRY_API_KEY environment variable is not set. Aborting.")
        return 1
    
    # 2. Load Target Species
    try:
        target_species = load_target_species_list()
    except (FileNotFoundError, ValueError) as e:
        logger.error(f"Failed to load target species list: {e}")
        # Initialize empty summary to allow fallback to proceed
        summary = {
            "target_species": [],
            "primary_source_results": {},
            "missing_from_try": [],
            "error": str(e)
        }
        save_trait_fallback_summary(summary, OUTPUT_FILE)
        return 1
    
    if not target_species:
        logger.warning("No target species found. Writing empty summary.")
        summary = {
            "target_species": [],
            "primary_source_results": {},
            "missing_from_try": [],
            "note": "No target species provided."
        }
        save_trait_fallback_summary(summary, OUTPUT_FILE)
        return 0
    
    # 3. Fetch Data
    try:
        summary = compile_try_results(target_species, api_key)
    except Exception as e:
        logger.critical(f"Unexpected error during data compilation: {e}")
        # Write partial or error state to allow pipeline to continue to fallback
        summary = {
            "target_species": target_species,
            "primary_source_results": {},
            "missing_from_try": target_species,
            "error": str(e)
        }
    
    # 4. Save Output
    save_trait_fallback_summary(summary, OUTPUT_FILE)
    
    logger.info(f"T025a completed. Found traits for {len(summary['primary_source_results'])} species. Missing: {len(summary['missing_from_try'])}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
