"""
Traits Fallback Module (T025b)

Fetches defense trait data from Phenoscape and GBIF for species missing from TRY.
Updates the trait_fallback_summary.json with results.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import requests
from urllib.parse import quote

# Import from project utils
from src.utils.logger import get_logger
from src.utils.config import get_data_path

# Initialize logger
logger = get_logger(__name__)

# Constants
PHENOSCAPE_API_BASE = "https://kb.phenoscape.org/api"
GBIF_API_BASE = "https://api.gbif.org/v1"

# Defense traits we are interested in (simplified list for fallback)
DEFENSE_TRAIT_IDS = [
    "chemical_defense",
    "physical_defense", 
    "thorns",
    "trichomes",
    "secondary_metabolites"
]

def load_fallback_input() -> Dict[str, Any]:
    """
    Load the input data from T025a output.
    
    Reads data/processed/post_qc_species_list.json and data/processed/trait_fallback_summary.json
    to identify species that need fallback trait fetching.
    
    Returns:
        Dict containing target species list and missing species from TRY
    """
    data_path = get_data_path()
    processed_path = Path(data_path) / "processed"
    
    # Load target species list
    species_list_path = processed_path / "post_qc_species_list.json"
    if not species_list_path.exists():
        raise FileNotFoundError(f"Target species list not found: {species_list_path}")
    
    with open(species_list_path, 'r') as f:
        species_data = json.load(f)
    
    # Extract unique species names
    target_species = []
    if isinstance(species_data, list):
        for item in species_data:
            if isinstance(item, dict) and 'species' in item:
                target_species.append(item['species'])
            elif isinstance(item, str):
                target_species.append(item)
    elif isinstance(species_data, dict):
        target_species = list(species_data.get('species', []))
    
    # Load existing fallback summary to get missing_from_try list
    summary_path = processed_path / "trait_fallback_summary.json"
    missing_from_try = []
    
    if summary_path.exists():
        with open(summary_path, 'r') as f:
            summary_data = json.load(f)
            missing_from_try = summary_data.get('missing_from_try', [])
    else:
        # If summary doesn't exist, assume all target species are missing
        missing_from_try = target_species
    
    return {
        'target_species': target_species,
        'missing_from_try': missing_from_try,
        'processed_path': processed_path
    }

def fetch_traits_from_phenoscape(species_name: str) -> Optional[Dict[str, Any]]:
    """
    Fetch defense traits for a species from Phenoscape knowledge base.
    
    Args:
        species_name: Scientific name of the species
        
    Returns:
        Dictionary with trait data or None if not found
    """
    try:
        # Phenoscape search for species
        search_url = f"{PHENOSCAPE_API_BASE}/taxon/search"
        params = {'q': species_name, 'limit': 1}
        
        response = requests.get(search_url, params=params, timeout=10)
        
        if response.status_code != 200:
            logger.warning(f"Phenoscape search failed for {species_name}: {response.status_code}")
            return None
        
        search_results = response.json()
        
        if not search_results or 'results' not in search_results or len(search_results['results']) == 0:
            logger.debug(f"No Phenoscape taxon match for {species_name}")
            return None
        
        taxon_id = search_results['results'][0].get('id')
        if not taxon_id:
            return None
        
        # Fetch trait data for this taxon
        traits_url = f"{PHENOSCAPE_API_BASE}/taxon/{taxon_id}/traits"
        traits_response = requests.get(traits_url, timeout=10)
        
        if traits_response.status_code != 200:
            return None
        
        traits_data = traits_response.json()
        
        # Extract relevant defense traits
        defense_traits = {}
        for trait in traits_data.get('traits', []):
            trait_label = trait.get('label', '').lower()
            if any(defense_keyword in trait_label for defense_keyword in 
                   ['defense', 'thorn', 'spine', 'trichome', 'chemical', 'physical']):
                defense_traits[trait_label] = {
                    'value': trait.get('value'),
                    'evidence': trait.get('evidence', [])
                }
        
        if defense_traits:
            return {
                'source': 'phenoscape',
                'species': species_name,
                'traits': defense_traits,
                'found': True
            }
        
        return None
        
    except requests.RequestException as e:
        logger.error(f"Phenoscape API error for {species_name}: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching from Phenoscape for {species_name}: {str(e)}")
        return None

def fetch_traits_from_gbif(species_name: str) -> Optional[Dict[str, Any]]:
    """
    Fetch defense-related trait data for a species from GBIF.
    
    Note: GBIF doesn't have direct defense trait endpoints, but we can check
    for occurrence data and associated trait datasets.
    
    Args:
        species_name: Scientific name of the species
        
    Returns:
        Dictionary with trait data or None if not found
    """
    try:
        # First, get the species key from GBIF
        search_url = f"{GBIF_API_BASE}/species/search"
        params = {'q': species_name, 'limit': 1}
        
        response = requests.get(search_url, params=params, timeout=10)
        
        if response.status_code != 200:
            logger.warning(f"GBIF search failed for {species_name}: {response.status_code}")
            return None
        
        search_results = response.json()
        
        if not search_results.get('results'):
            return None
        
        species_key = search_results['results'][0].get('key')
        if not species_key:
            return None
        
        # Check for associated traits (GBIF trait API is limited)
        # We'll use occurrence data as a proxy for data availability
        occurrence_url = f"{GBIF_API_BASE}/occurrence/search"
        params = {
            'species_key': species_key,
            'limit': 1,
            'hasCoordinate': True
        }
        
        occurrence_response = requests.get(occurrence_url, params=params, timeout=10)
        
        if occurrence_response.status_code != 200:
            return None
        
        occurrence_data = occurrence_response.json()
        
        # If we have occurrences, we can consider the species as having data
        # This is a proxy since GBIF doesn't have direct defense trait endpoints
        total_count = occurrence_data.get('count', 0)
        
        if total_count > 0:
            return {
                'source': 'gbif',
                'species': species_name,
                'traits': {
                    'data_availability': 'high' if total_count > 100 else 'moderate',
                    'occurrence_count': total_count,
                    'note': 'GBIF provides occurrence data, not direct defense traits'
                },
                'found': True
            }
        
        return None
        
    except requests.RequestException as e:
        logger.error(f"GBIF API error for {species_name}: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching from GBIF for {species_name}: {str(e)}")
        return None

def fetch_traits_for_species(species_name: str) -> Dict[str, Any]:
    """
    Attempt to fetch traits from both Phenoscape and GBIF for a species.
    
    Args:
        species_name: Scientific name of the species
        
    Returns:
        Dictionary with results from both sources
    """
    logger.info(f"Fetching fallback traits for: {species_name}")
    
    result = {
        'species': species_name,
        'phenoscape': None,
        'gbif': None,
        'found_any': False
    }
    
    # Try Phenoscape first
    phenoscape_traits = fetch_traits_from_phenoscape(species_name)
    if phenoscape_traits:
        result['phenoscape'] = phenoscape_traits
        result['found_any'] = True
        logger.info(f"Found traits for {species_name} in Phenoscape")
    
    # Try GBIF
    gbif_traits = fetch_traits_from_gbif(species_name)
    if gbif_traits:
        result['gbif'] = gbif_traits
        result['found_any'] = True
        logger.info(f"Found traits/data for {species_name} in GBIF")
    
    return result

def save_trait_fallback_summary(summary_data: Dict[str, Any], processed_path: Path) -> None:
    """
    Save the updated trait fallback summary to JSON.
    
    Args:
        summary_data: Complete summary data including fallback results
        processed_path: Path to processed data directory
    """
    output_path = processed_path / "trait_fallback_summary.json"
    
    with open(output_path, 'w') as f:
        json.dump(summary_data, f, indent=2)
    
    logger.info(f"Saved trait fallback summary to {output_path}")

def main() -> int:
    """
    Main entry point for the traits fallback task.
    
    Returns:
        0 on success, 1 on error
    """
    try:
        logger.info("Starting traits fallback data fetching (T025b)")
        
        # Load input data
        input_data = load_fallback_input()
        target_species = input_data['target_species']
        missing_from_try = input_data['missing_from_try']
        processed_path = input_data['processed_path']
        
        logger.info(f"Processing {len(missing_from_try)} species missing from TRY")
        
        # Load existing summary or create new one
        summary_path = processed_path / "trait_fallback_summary.json"
        
        if summary_path.exists():
            with open(summary_path, 'r') as f:
                summary = json.load(f)
        else:
            summary = {
                'target_species': target_species,
                'primary_source_results': {},
                'missing_from_try': missing_from_try,
                'missing_from_all_sources': [],
                'fallback_results': {}
            }
        
        # Track species found in fallback sources
        species_found_in_fallback = []
        fallback_results = {}
        
        # Fetch traits for each missing species
        for species in missing_from_try:
            logger.info(f"Fetching fallback traits for: {species}")
            
            species_result = fetch_traits_for_species(species)
            
            if species_result['found_any']:
                species_found_in_fallback.append(species)
                fallback_results[species] = species_result
            else:
                # Species not found in any fallback source
                if 'missing_from_all_sources' not in summary:
                    summary['missing_from_all_sources'] = []
                if species not in summary['missing_from_all_sources']:
                    summary['missing_from_all_sources'].append(species)
        
        # Update summary with fallback results
        summary['fallback_results'] = fallback_results
        summary['species_found_in_fallback'] = species_found_in_fallback
        
        # Update missing_from_try list (remove species found in fallback)
        summary['missing_from_try'] = [
            species for species in missing_from_try 
            if species not in species_found_in_fallback
        ]
        
        # Save updated summary
        save_trait_fallback_summary(summary, processed_path)
        
        logger.info(f"Fallback complete: {len(species_found_in_fallback)} species found")
        logger.info(f"Still missing from all sources: {len(summary['missing_from_all_sources'])}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error in traits fallback task: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return 1

if __name__ == "__main__":
    sys.exit(main())
