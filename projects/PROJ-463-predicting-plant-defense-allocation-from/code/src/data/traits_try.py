"""
T025a: Fetch defense trait data from TRY database (Primary Source).

This module implements the primary data acquisition for plant defense traits.
It reads target species from the QC output, attempts to fetch data from the
TRY database, and initializes the fallback summary report.
"""

import os
import sys
import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import requests

from src.utils.config import get_data_path
from src.utils.logger import get_logger

# Configure logging
logger = get_logger(__name__)

# Constants
TRY_BASE_URL = "https://www.try-db.org/api/v1"
TRY_TIMEOUT = 30
RATE_LIMIT_DELAY = 1.0  # seconds between requests

# Trait mappings (TRY trait IDs or search terms)
# Note: Actual IDs may vary; this uses a heuristic mapping based on common trait names
TARGET_TRAITS = {
    "Glucosinolates": {"trait_name": "Glucosinolates", "trait_id": None},
    "Alkaloids": {"trait_name": "Alkaloids", "trait_id": None},
    "Phenolics": {"trait_name": "Phenolics", "trait_id": None},
    "Trichome Density": {"trait_name": "Trichome density", "trait_id": None},
    "Leaf Tensile Strength": {"trait_name": "Leaf tensile strength", "trait_id": None},
}

def load_target_species_list() -> List[str]:
    """
    Load the target species list from the QC output file.

    Returns:
        List[str]: List of species names.

    Raises:
        FileNotFoundError: If the QC output file is missing.
        ValueError: If the file content is invalid.
    """
    qc_output_path = get_data_path("processed/post_qc_species_list.json")
    
    if not os.path.exists(qc_output_path):
        logger.error(f"Target species list not found at {qc_output_path}. "
                     "Ensure T014 (QC) has been completed successfully.")
        raise FileNotFoundError(f"Target species list file not found: {qc_output_path}")

    try:
        with open(qc_output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle different possible structures
        if isinstance(data, list):
            return [item.get('species', item) if isinstance(item, dict) else item for item in data]
        elif isinstance(data, dict) and 'species' in data:
            return data['species']
        elif isinstance(data, dict) and 'included_species' in data:
            return data['included_species']
        else:
            # Try to extract species keys if it's a dict of species data
            if all(isinstance(v, dict) for v in data.values()):
                return list(data.keys())
            else:
                raise ValueError("Unexpected structure in post_qc_species_list.json")
                
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in target species list: {e}")
        raise
    except Exception as e:
        logger.error(f"Error reading target species list: {e}")
        raise

def create_retry_session(max_retries: int = 3) -> requests.Session:
    """
    Create a requests session with retry logic.

    Args:
        max_retries: Maximum number of retry attempts.

    Returns:
        requests.Session: Configured session.
    """
    session = requests.Session()
    retry_config = {
        'total': max_retries,
        'backoff_factor': 0.5,
        'status_forcelist': [429, 500, 502, 503, 504],
    }
    
    try:
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        
        retry = Retry(**retry_config)
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
    except ImportError:
        logger.warning("urllib3 not available, retry logic disabled")
    
    return session

def fetch_traits_for_species(
    species_name: str, 
    session: requests.Session,
    api_key: Optional[str] = None
) -> Tuple[Optional[List[Dict]], str]:
    """
    Fetch defense traits for a single species from TRY database.

    Args:
        species_name: Scientific name of the species.
        session: Requests session with retry logic.
        api_key: Optional API key for authentication.

    Returns:
        Tuple of (list of traits or None, status message)
    """
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    
    # Try multiple search strategies
    search_terms = [
        species_name,
        species_name.replace('_', ' '),
        species_name.split()[0] if ' ' in species_name else species_name, # Genus only
    ]

    for term in search_terms:
        try:
            # Attempt to search for traits
            search_url = f"{TRY_BASE_URL}/traits/search"
            params = {
                "query": term,
                "limit": 50,
            }
            
            logger.info(f"Searching TRY for species: {term}")
            response = session.get(search_url, headers=headers, params=params, timeout=TRY_TIMEOUT)
            
            if response.status_code == 401:
                logger.error("TRY API authentication failed. Check TRY_API_KEY.")
                return None, "AUTH_FAILED"
            elif response.status_code == 404:
                continue  # Try next search term
            elif response.status_code != 200:
                logger.warning(f"TRY API returned {response.status_code} for {term}")
                continue

            data = response.json()
            
            # Extract traits if found
            if 'data' in data and len(data['data']) > 0:
                traits = []
                for item in data['data']:
                    # Map to our standard schema
                    trait_entry = {
                        "trait_id": item.get('id'),
                        "trait_name": item.get('name', 'Unknown'),
                        "value": item.get('value'),
                        "unit": item.get('unit'),
                        "source": "TRY",
                        "species": species_name,
                    }
                    # Only include if value is present
                    if trait_entry['value'] is not None:
                        traits.append(trait_entry)
                
                if traits:
                    return traits, "SUCCESS"
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"Network error searching TRY for {term}: {e}")
            continue
        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON response from TRY for {term}: {e}")
            continue
        except Exception as e:
            logger.warning(f"Unexpected error searching TRY for {term}: {e}")
            continue

    return None, "NOT_FOUND"

def compile_try_results(
    species_list: List[str],
    api_key: Optional[str] = None
) -> Tuple[Dict[str, List[Dict]], List[str], bool]:
    """
    Compile TRY results for all target species.

    Args:
        species_list: List of species names to query.
        api_key: Optional API key.

    Returns:
        Tuple of (results_dict, missing_species_list, api_key_status)
    """
    results = {}
    missing_species = []
    api_key_status = "present" if api_key else "missing"

    session = create_retry_session()
    
    for species in species_list:
        logger.info(f"Fetching traits for {species} from TRY...")
        
        traits, status = fetch_traits_for_species(species, session, api_key)
        
        if status == "AUTH_FAILED":
            logger.error("Authentication failed for TRY API.")
            api_key_status = "invalid"
            # Continue with other species but note the auth failure
            traits = None
        
        if traits:
            results[species] = traits
            logger.info(f"Found {len(traits)} traits for {species}")
        else:
            missing_species.append(species)
            logger.info(f"No traits found for {species} in TRY")
        
        # Rate limiting
        time.sleep(RATE_LIMIT_DELAY)

    return results, missing_species, api_key_status

def save_trait_fallback_summary(
    target_species: List[str],
    primary_results: Dict[str, List[Dict]],
    missing_from_try: List[str],
    api_key_status: str
) -> str:
    """
    Save the initial trait fallback summary with TRY results.

    Args:
        target_species: List of all target species.
        primary_results: Results from TRY database.
        missing_from_try: List of species not found in TRY.
        api_key_status: Status of the API key (present/missing/invalid).

    Returns:
        Path to the saved summary file.
    """
    output_path = get_data_path("processed/trait_fallback_summary.json")
    
    summary = {
        "target_species": target_species,
        "primary_source_results": primary_results,
        "missing_from_try": missing_from_try,
        "missing_from_all_sources": [],  # Will be updated by T025b
        "try_api_key_status": api_key_status,
        "metadata": {
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "source": "TRY",
            "status": "initialized"
        }
    }

    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Saved trait fallback summary to {output_path}")
    return output_path

def main():
    """
    Main entry point for T025a: Fetch traits from TRY database.
    """
    logger.info("Starting T025a: Fetch defense traits from TRY database")
    
    try:
        # 1. Load target species
        logger.info("Loading target species list...")
        target_species = load_target_species_list()
        logger.info(f"Found {len(target_species)} target species")
        
        if not target_species:
            logger.warning("No target species found. Creating empty summary.")
            save_trait_fallback_summary([], {}, [], "no_species")
            return 0

        # 2. Check for API key
        api_key = os.environ.get("TRY_API_KEY")
        if not api_key:
            logger.warning("TRY_API_KEY environment variable not set. "
                         "Fetching may fail or return limited data.")
        
        # 3. Fetch traits from TRY
        logger.info("Fetching traits from TRY database...")
        try_results, missing_species, api_key_status = compile_try_results(
            target_species, api_key
        )
        
        # 4. Save summary
        logger.info("Saving trait fallback summary...")
        output_path = save_trait_fallback_summary(
            target_species,
            try_results,
            missing_species,
            api_key_status
        )
        
        logger.info(f"T025a completed successfully. Output: {output_path}")
        
        # Log summary stats
        found_count = len(try_results)
        missing_count = len(missing_species)
        logger.info(f"Results: {found_count} species with traits, "
                   f"{missing_count} species missing from TRY")
        
        return 0

    except FileNotFoundError as e:
        logger.error(f"Required input file missing: {e}")
        logger.error("T014 (QC) must be completed first to generate post_qc_species_list.json")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error in T025a: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1

if __name__ == "__main__":
    sys.exit(main())
