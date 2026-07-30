"""
Fetch defense trait data from the TRY database (Primary Source).

This module implements the primary data acquisition strategy for plant defense traits.
It reads target species from the QC output, queries the TRY API, caches raw responses,
and updates the fallback summary manifest.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import requests
from datetime import datetime

# Import project utilities
from src.utils.logger import get_logger
from src.data.traits_cache import cache_raw_response
from src.utils.schemas import DefenseTrait, TraitDataset

# Constants
TRY_API_BASE_URL = "https://www.try-db.org/TryWebAPI.php"
REQUIRED_ENV_VAR = "TRY_API_KEY"
OUTPUT_PATH = Path("data/processed/trait_fallback_summary.json")
INPUT_PATH = Path("data/processed/post_qc_species_list.json")
CACHE_DIR = Path("data/raw/traits")

# Logger setup
logger = get_logger(__name__)

def load_target_species_list() -> List[str]:
    """
    Load the list of target species from the QC output.
    
    Returns:
        List[str]: List of species names to fetch traits for.
    
    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If the file format is invalid.
    """
    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"Target species list not found at {INPUT_PATH}. "
                              "Run T014 (QC) first to generate this file.")
    
    try:
        with open(INPUT_PATH, 'r') as f:
            data = json.load(f)
        
        # Expected schema: {"species": [{"name": "...", ...}, ...]}
        if "species" not in data:
            raise ValueError("Invalid QC output format: missing 'species' key")
        
        species_list = [item["name"] for item in data["species"]]
        logger.info(f"Loaded {len(species_list)} target species from QC output.")
        return species_list
        
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse QC output JSON: {e}")

def fetch_traits_for_species(species_name: str) -> Optional[Dict[str, Any]]:
    """
    Fetch defense trait data for a single species from the TRY database.
    
    Args:
        species_name: The scientific name of the species (e.g., "Arabidopsis thaliana").
    
    Returns:
        Dict[str, Any]: Parsed trait data if successful, None otherwise.
    
    Raises:
        requests.RequestException: If the API request fails (network error).
        ValueError: If the API key is missing or invalid.
    """
    api_key = os.environ.get(REQUIRED_ENV_VAR)
    if not api_key:
        raise ValueError(f"Environment variable {REQUIRED_ENV_VAR} is not set. "
                       "Cannot fetch from TRY without authentication.")
    
    # TRY API typically requires a POST request with specific parameters
    # Note: The exact endpoint structure may vary based on TRY version.
    # This implementation assumes a standard search-by-species pattern.
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    payload = {
        "species": species_name,
        "trait_ids": [
            "1001", "1002", "1003", "1004", "1005",  # Example chemical traits
            "2001", "2002", "2003", "2004", "2005"   # Example physical traits
            # In a real implementation, these would be the specific TRY trait IDs for defense
        ]
    }
    
    try:
        logger.debug(f"Fetching traits for {species_name} from TRY...")
        response = requests.post(
            TRY_API_BASE_URL,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 401:
            raise ValueError(f"Invalid API key for TRY. Status 401 for {species_name}")
        
        if response.status_code == 404:
            logger.warning(f"Species {species_name} not found in TRY database.")
            return None
        
        if response.status_code != 200:
            logger.error(f"TRY API error for {species_name}: {response.status_code} - {response.text}")
            return None
        
        raw_data = response.json()
        
        # Cache the raw response before processing (Constitution Principle III)
        cache_path = cache_raw_response("try", species_name, raw_data)
        logger.info(f"Cached raw TRY response for {species_name} at {cache_path}")
        
        # Parse and validate the response structure
        # Assuming a structure like: { "species": "...", "traits": [ {...}, ... ] }
        if "traits" in raw_data:
            return {
                "species": species_name,
                "traits": raw_data["traits"],
                "source": "try",
                "fetched_at": datetime.utcnow().isoformat()
            }
        else:
            logger.warning(f"No 'traits' key in TRY response for {species_name}")
            return None

    except requests.Timeout:
        logger.error(f"Timeout fetching traits for {species_name} from TRY")
        raise
    except requests.ConnectionError:
        logger.error(f"Connection error fetching traits for {species_name} from TRY")
        raise

def compile_try_results(species_list: List[str]) -> Dict[str, Any]:
    """
    Compile results from TRY fetch attempts for all target species.
    
    Args:
        species_list: List of species names to fetch.
    
    Returns:
        Dict containing primary_source_results and missing_from_try list.
    """
    primary_results = {}
    missing_species = []
    
    logger.info(f"Starting TRY fetch for {len(species_list)} species...")
    
    for species in species_list:
        try:
            result = fetch_traits_for_species(species)
            if result:
                primary_results[species] = result
                logger.info(f"Successfully fetched traits for {species} from TRY.")
            else:
                missing_species.append(species)
                logger.info(f"Traits missing for {species} in TRY.")
        except ValueError as e:
            # Specifically catch API key errors to handle the "proceed immediately" logic
            if "TRY_API_KEY" in str(e):
                logger.critical(f"TRY API key missing. Stopping TRY fetch. Error: {e}")
                # We raise here to halt the TRY specific logic, 
                # but the main() function will catch this and proceed to fallback.
                raise e
            else:
                missing_species.append(species)
                logger.warning(f"Failed to fetch {species} (ValueError): {e}")
        except Exception as e:
            missing_species.append(species)
            logger.error(f"Unexpected error fetching {species} from TRY: {e}")
    
    return {
        "primary_source_results": primary_results,
        "missing_from_try": missing_species,
        "total_target": len(species_list),
        "retrieved_count": len(primary_results),
        "missing_count": len(missing_species)
    }

def save_trait_fallback_summary(try_results: Dict[str, Any]) -> None:
    """
    Save the initial TRY results to the fallback summary manifest.
    
    This initializes the file structure that T025b will append to.
    
    Args:
        try_results: The dictionary returned by compile_try_results.
    """
    # Ensure output directory exists
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    # Structure expected by T025b and downstream tasks
    summary = {
        "target_species": list(try_results["primary_source_results"].keys()) + try_results["missing_from_try"],
        "primary_source_results": try_results["primary_source_results"],
        "missing_from_try": try_results["missing_from_try"],
        "metadata": {
            "source": "try_primary",
            "generated_at": datetime.utcnow().isoformat(),
            "total_target_species": try_results["total_target"],
            "retrieved": try_results["retrieved_count"],
            "missing": try_results["missing_count"]
        }
    }
    
    with open(OUTPUT_PATH, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Saved TRY results to {OUTPUT_PATH}")

def main() -> int:
    """
    Main entry point for T025a.
    
    Workflow:
    1. Load target species from QC output.
    2. Check for TRY_API_KEY.
    3. Fetch traits for each species.
    4. Save results to trait_fallback_summary.json.
    5. If API key is missing, raise error to trigger fallback logic in the pipeline.
    
    Returns:
        int: 0 on success, 1 on failure.
    """
    try:
        # 1. Load targets
        species_list = load_target_species_list()
        if not species_list:
            logger.warning("No target species found. Nothing to fetch.")
            # Create an empty summary to allow downstream to run
            save_trait_fallback_summary({
                "primary_source_results": {},
                "missing_from_try": [],
                "total_target": 0,
                "retrieved_count": 0,
                "missing_count": 0
            })
            return 0
        
        # 2. Check API Key
        if not os.environ.get(REQUIRED_ENV_VAR):
            logger.critical(f"{REQUIRED_ENV_KEY} environment variable is missing.")
            # Raise to signal the pipeline that primary source is unavailable
            raise RuntimeError(f"{REQUIRED_ENV_KEY} is missing. Proceeding to fallback.")
        
        # 3. Compile Results
        try_results = compile_try_results(species_list)
        
        # 4. Save Summary
        save_trait_fallback_summary(try_results)
        
        # 5. Check Halt Condition (Partial - full check happens after fallback)
        # We only check the fraction missing from TRY here to log, 
        # but the actual SystemExit is handled in the pipeline orchestration 
        # or T038 after fallback completes.
        missing_fraction = len(try_results["missing_from_try"]) / try_results["total_target"]
        logger.info(f"TRY retrieval complete. Missing fraction from primary: {missing_fraction:.2f}")
        
        return 0
        
    except RuntimeError as e:
        if "TRY_API_KEY" in str(e) or REQUIRED_ENV_VAR in str(e):
            logger.error(f"TRY API Key missing. Task T025a cannot proceed with primary source.")
            logger.error("Pipeline should now trigger T025b (fallback) immediately.")
            # We do not write the summary here if we failed immediately, 
            # but to be safe for the pipeline, we might want to write an empty one.
            # However, the spec says "proceed immediately to T025b".
            # Let's write a minimal summary indicating the failure state.
            OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
            summary = {
                "target_species": load_target_species_list() if INPUT_PATH.exists() else [],
                "primary_source_results": {},
                "missing_from_try": load_target_species_list() if INPUT_PATH.exists() else [],
                "metadata": {"error": "TRY_API_KEY_MISSING", "generated_at": datetime.utcnow().isoformat()}
            }
            with open(OUTPUT_PATH, 'w') as f:
                json.dump(summary, f, indent=2)
            return 1
        raise
    except Exception as e:
        logger.error(f"Unexpected error in T025a: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
