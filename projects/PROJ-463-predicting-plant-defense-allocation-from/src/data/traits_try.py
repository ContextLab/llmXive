import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import requests

# Add parent directory to path to allow imports from src
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.logger import get_logger
from src.data.traits_cache import cache_raw_response

# Configure logging
logger = get_logger(__name__)

# TRY Database Configuration
TRY_API_BASE_URL = "https://www.try-db.org/api/v1"
DEFENSE_TRAIT_IDS = [
    "1", "2", "3", "4", "5", "6", "7", "8", "9", "10",  # Chemical defense traits
    "11", "12", "13", "14", "15", "16", "17", "18", "19", "20"  # Physical defense traits
]

def load_target_species_list(input_path: str = "data/processed/post_qc_species_list.json") -> List[str]:
    """
    Load the target species list from the post-QC species list file.
    
    Args:
        input_path: Path to the post_qc_species_list.json file
        
    Returns:
        List of species names
        
    Raises:
        FileNotFoundError: If the input file does not exist
        json.JSONDecodeError: If the file is not valid JSON
    """
    input_file = Path(input_path)
    if not input_file.exists():
        raise FileNotFoundError(f"Target species list not found at {input_path}")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Extract species names from the list
    species_list = [item['name'] for item in data.get('species', []) if item.get('exclusion_reason') is None]
    return species_list

def fetch_traits_for_species(species_name: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Fetch defense trait data for a single species from the TRY database.
    
    Args:
        species_name: The scientific name of the species
        api_key: Optional API key for authentication
        
    Returns:
        Dictionary containing trait data or error information
    """
    headers = {}
    if api_key:
        headers['Authorization'] = f'Bearer {api_key}'
    
    # Construct the API request URL
    # Note: TRY API endpoint structure may vary; using a generic pattern
    url = f"{TRY_API_BASE_URL}/species/search"
    params = {
        'scientific_name': species_name,
        'trait_ids': ','.join(DEFENSE_TRAIT_IDS)
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Cache the raw response
        cache_raw_response('try', species_name, response.json())
        
        return {
            'success': True,
            'species': species_name,
            'traits': response.json(),
            'source': 'try'
        }
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            logger.warning(f"Authentication failed for {species_name} from TRY: Invalid API key")
            return {
                'success': False,
                'species': species_name,
                'error': 'Authentication failed',
                'source': 'try'
            }
        elif e.response.status_code == 404:
            logger.info(f"Species {species_name} not found in TRY database")
            return {
                'success': False,
                'species': species_name,
                'error': 'Species not found',
                'source': 'try'
            }
        else:
            logger.error(f"HTTP error fetching {species_name} from TRY: {e}")
            return {
                'success': False,
                'species': species_name,
                'error': f'HTTP error: {e.response.status_code}',
                'source': 'try'
            }
    except requests.exceptions.Timeout:
        logger.error(f"Timeout fetching {species_name} from TRY")
        return {
            'success': False,
            'species': species_name,
            'error': 'Request timeout',
            'source': 'try'
        }
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error fetching {species_name} from TRY: {e}")
        return {
            'success': False,
            'species': species_name,
            'error': f'Request error: {str(e)}',
            'source': 'try'
        }

def compile_try_results(species_results: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """
    Compile TRY results to identify missing species.
    
    Args:
        species_results: List of result dictionaries from fetch_traits_for_species
        
    Returns:
        Dictionary with 'found' and 'missing' lists
    """
    found = []
    missing = []
    
    for result in species_results:
        if result.get('success'):
            found.append(result['species'])
        else:
            missing.append(result['species'])
    
    return {
        'found': found,
        'missing': missing
    }

def save_trait_fallback_summary(
    target_species: List[str],
    primary_source_results: Dict[str, Dict[str, Any]],
    missing_from_try: List[str],
    missing_from_all_sources: List[str],
    output_path: str = "data/processed/trait_fallback_summary.json",
    try_api_key_status: str = "present"
) -> None:
    """
    Save the trait fallback summary JSON file.
    
    Args:
        target_species: List of all target species
        primary_source_results: Results from TRY database
        missing_from_try: List of species missing from TRY
        missing_from_all_sources: List of species missing from all sources (empty at this stage)
        output_path: Path to write the summary file
        try_api_key_status: Status of the TRY API key ("present" or "missing")
    """
    summary = {
        'target_species': target_species,
        'primary_source_results': primary_source_results,
        'missing_from_try': missing_from_try,
        'missing_from_all_sources': missing_from_all_sources,
        'try_api_key_status': try_api_key_status,
        'generated_at': __import__('datetime').datetime.now().isoformat()
    }
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Trait fallback summary saved to {output_path}")

def main() -> int:
    """
    Main function to fetch defense trait data from TRY database.
    
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        # Load target species list
        species_list = load_target_species_list()
        logger.info(f"Loaded {len(species_list)} target species")
        
        # Check for TRY API key
        api_key = os.environ.get('TRY_API_KEY')
        try_api_key_status = "present" if api_key else "missing"
        
        if not api_key:
            logger.warning("TRY_API_KEY environment variable is missing. Proceeding without authentication.")
        
        # Fetch traits for each species
        primary_source_results = {}
        species_results = []
        
        for species in species_list:
            logger.info(f"Fetching traits for {species} from TRY...")
            result = fetch_traits_for_species(species, api_key)
            species_results.append(result)
            primary_source_results[species] = result
        
        # Compile results
        compiled = compile_try_results(species_results)
        missing_from_try = compiled['missing']
        
        # Initialize missing_from_all_sources as empty (will be updated by T025b)
        missing_from_all_sources = []
        
        # Save the summary
        save_trait_fallback_summary(
            target_species=species_list,
            primary_source_results=primary_source_results,
            missing_from_try=missing_from_try,
            missing_from_all_sources=missing_from_all_sources,
            try_api_key_status=try_api_key_status
        )
        
        logger.info(f"TRY fetch complete. Found traits for {len(compiled['found'])} species.")
        logger.info(f"Missing from TRY: {len(missing_from_try)} species")
        
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Input file not found: {e}")
        return 1
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in input file: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error in main: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())