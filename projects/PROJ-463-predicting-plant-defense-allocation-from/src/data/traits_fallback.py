"""
Fallback trait data acquisition from Phenoscape and GBIF.

This module implements the fallback strategy for fetching plant defense traits
when the primary TRY database fails or returns missing data.

Sources:
- Phenoscape KB API (https://phenoscape.org/api/)
- GBIF Species API (https://www.gbif.org/developer/species)

Output:
- Updates data/processed/trait_fallback_summary.json with fallback_results
- Raises SystemExit if missing fraction > 30% after fallback
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import requests
from urllib.parse import quote
from datetime import datetime

# Project imports matching existing API surface
from src.utils.logger import get_logger
from src.utils.config import get_data_path

# Initialize logger
logger = get_logger(__name__)

# Constants
PHENOSCAPE_API_BASE = "https://phenoscape.org/api"
GBIF_API_BASE = "https://api.gbif.org/v1"
FALLBACK_SUMMARY_PATH = "data/processed/trait_fallback_summary.json"
POST_QC_SPECIES_PATH = "data/processed/post_qc_species_list.json"
MISSING_THRESHOLD = 0.30

def load_fallback_input() -> Dict[str, Any]:
    """
    Load the fallback input from T025a output.
    
    Returns:
        Dictionary containing target_species list and missing_from_try list.
        
    Raises:
        FileNotFoundError: If the input file does not exist.
        json.JSONDecodeError: If the input file is not valid JSON.
    """
    data_path = get_data_path()
    input_file = data_path / FALLBACK_SUMMARY_PATH
    
    if not input_file.exists():
        logger.error(f"Fallback input file not found: {input_file}")
        raise FileNotFoundError(f"Fallback input file not found: {input_file}")
    
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    if 'target_species' not in data:
        raise ValueError("Input file missing 'target_species' key")
    if 'missing_from_try' not in data:
        raise ValueError("Input file missing 'missing_from_try' key")
    
    return data

def fetch_traits_from_phenoscape(species_name: str) -> Optional[Dict[str, Any]]:
    """
    Fetch defense trait data for a species from Phenoscape KB API.
    
    Phenoscape KB contains phenotype data linked to taxa. We search for
    plant defense-related phenotypes (chemical defenses, physical defenses).
    
    Args:
        species_name: Scientific name of the species (e.g., "Arabidopsis thaliana")
        
    Returns:
        Dictionary with trait data if found, None otherwise.
    """
    try:
        # Search for the taxon in Phenoscape
        # Phenoscape uses taxon IDs, so we first need to find the taxon
        taxon_search_url = f"{PHENOSCAPE_API_BASE}/taxa/search"
        params = {'q': species_name, 'format': 'json'}
        
        logger.debug(f"Querying Phenoscape for taxon: {species_name}")
        response = requests.get(taxon_search_url, params=params, timeout=30)
        response.raise_for_status()
        
        taxon_data = response.json()
        
        if not taxon_data or 'results' not in taxon_data or len(taxon_data['results']) == 0:
            logger.debug(f"No Phenoscape taxon found for: {species_name}")
            return None
        
        # Use the first matching taxon ID
        taxon_id = taxon_data['results'][0].get('id')
        if not taxon_id:
            return None
        
        # Fetch phenotypes for this taxon
        phenotype_url = f"{PHENOSCAPE_API_BASE}/taxa/{taxon_id}/phenotypes"
        response = requests.get(phenotype_url, timeout=30)
        response.raise_for_status()
        
        phenotype_data = response.json()
        
        # Extract defense-related traits
        defense_traits = {
            'chemical_defenses': [],
            'physical_defenses': [],
            'source': 'phenoscape',
            'species': species_name,
            'taxon_id': taxon_id,
            'raw_count': 0
        }
        
        if 'results' in phenotype_data:
            for phenotype in phenotype_data['results']:
                # Look for defense-related keywords in phenotype labels
                label = phenotype.get('label', '').lower()
                
                # Simple keyword matching for defense traits
                defense_keywords = [
                    'toxin', 'alkaloid', 'terpenoid', 'phenolic', 'glucosinolate',
                    'trichome', 'thorn', 'spine', 'prickle', 'hair', 'latex',
                    'tannin', 'flavonoid', 'saponin', 'cyanogenic', 'defense'
                ]
                
                is_defense = any(keyword in label for keyword in defense_keywords)
                if is_defense:
                    trait_entry = {
                        'trait': label,
                        'value': phenotype.get('value', 'present'),
                        'source_annotation': phenotype.get('source', 'phenoscape_kb')
                    }
                    
                    # Categorize as chemical or physical
                    if any(kw in label for kw in ['toxin', 'alkaloid', 'terpenoid', 'phenolic', 
                                                   'glucosinolate', 'tannin', 'flavonoid', 
                                                   'saponin', 'cyanogenic']):
                        defense_traits['chemical_defenses'].append(trait_entry)
                    elif any(kw in label for kw in ['trichome', 'thorn', 'spine', 'prickle', 
                                                    'hair', 'latex']):
                        defense_traits['physical_defenses'].append(trait_entry)
                
                defense_traits['raw_count'] += 1
        
        # Only return if we found actual defense traits
        if defense_traits['chemical_defenses'] or defense_traits['physical_defenses']:
            logger.info(f"Found {len(defense_traits['chemical_defenses'])} chemical and "
                        f"{len(defense_traits['physical_defenses'])} physical traits from Phenoscape for {species_name}")
            return defense_traits
        else:
            return None
            
    except requests.exceptions.RequestException as e:
        logger.warning(f"Phenoscape API request failed for {species_name}: {e}")
        return None
    except Exception as e:
        logger.warning(f"Error processing Phenoscape data for {species_name}: {e}")
        return None

def fetch_traits_from_gbif(species_name: str) -> Optional[Dict[str, Any]]:
    """
    Fetch trait-related data for a species from GBIF.
    
    Note: GBIF primarily provides occurrence data and taxonomic information.
    We use it to verify species existence and potentially link to trait databases.
    For actual defense traits, we may need to use GBIF's integration with other
    databases or extract habitat-related proxies.
    
    Args:
        species_name: Scientific name of the species
        
    Returns:
        Dictionary with trait data if found, None otherwise.
    """
    try:
        # First, resolve the species name to a GBIF key
        species_search_url = f"{GBIF_API_BASE}/species/search"
        params = {
            'q': species_name,
            'limit': 1,
            'offset': 0
        }
        
        logger.debug(f"Querying GBIF for species: {species_name}")
        response = requests.get(species_search_url, params=params, timeout=30)
        response.raise_for_status()
        
        search_data = response.json()
        
        if not search_data.get('results'):
            logger.debug(f"No GBIF species found for: {species_name}")
            return None
        
        gbif_key = search_data['results'][0].get('key')
        if not gbif_key:
            return None
        
        # Fetch species details
        species_url = f"{GBIF_API_BASE}/species/{gbif_key}"
        response = requests.get(species_url, timeout=30)
        response.raise_for_status()
        
        species_data = response.json()
        
        # GBIF doesn't directly provide defense traits, but we can:
        # 1. Verify the species exists and is valid
        # 2. Extract habitat information as a proxy for defense strategy
        # 3. Check for links to trait databases (e.g., TRY, LEDA)
        
        defense_traits = {
            'chemical_defenses': [],
            'physical_defenses': [],
            'source': 'gbif',
            'species': species_name,
            'gbif_key': gbif_key,
            'habitat_info': {},
            'databases_linked': []
        }
        
        # Extract habitat information
        if 'vernacularNames' in species_data:
            defense_traits['vernacular_names'] = [
                v.get('name', '') for v in species_data['vernacularNames']
            ]
        
        # Check for associated databases
        if 'extensions' in species_data:
            for ext in species_data['extensions']:
                ext_type = ext.get('type', '')
                if 'trait' in ext_type.lower() or 'phenotype' in ext_type.lower():
                    defense_traits['databases_linked'].append(ext_type)
        
        # Extract habitat if available
        if 'habitat' in species_data:
            defense_traits['habitat_info'] = species_data['habitat']
        
        # GBIF rarely has direct defense trait data for plants
        # We return the verification data but note that it's limited
        if defense_traits['databases_linked'] or defense_traits['habitat_info']:
            logger.info(f"GBIF verification for {species_name} found habitat info and/or "
                        f"linked databases: {defense_traits['databases_linked']}")
            return defense_traits
        else:
            # Even if no traits, we confirm the species exists in GBIF
            # This is useful metadata but not trait data
            logger.debug(f"GBIF verified species {species_name} but found no trait proxies")
            return None
            
    except requests.exceptions.RequestException as e:
        logger.warning(f"GBIF API request failed for {species_name}: {e}")
        return None
    except Exception as e:
        logger.warning(f"Error processing GBIF data for {species_name}: {e}")
        return None

def fetch_traits_for_species(species_name: str) -> Dict[str, Any]:
    """
    Attempt to fetch traits for a species from both Phenoscape and GBIF.
    
    Args:
        species_name: Scientific name of the species
        
    Returns:
        Dictionary with results from both sources.
    """
    result = {
        'species': species_name,
        'phenoscape': None,
        'gbif': None,
        'found_traits': False
    }
    
    # Try Phenoscape first (more likely to have phenotype data)
    phenoscape_data = fetch_traits_from_phenoscape(species_name)
    if phenoscape_data:
        result['phenoscape'] = phenoscape_data
        result['found_traits'] = True
    
    # Try GBIF
    gbif_data = fetch_traits_from_gbif(species_name)
    if gbif_data:
        result['gbif'] = gbif_data
        # GBIF data is mostly verification, not traits
        if not result['found_traits'] and (gbif_data.get('databases_linked') or gbif_data.get('habitat_info')):
            result['found_traits'] = True  # Consider habitat/proxy data as partial success
    
    return result

def save_trait_fallback_summary(summary_data: Dict[str, Any]) -> Path:
    """
    Save the updated fallback summary to the output file.
    
    Args:
        summary_data: Complete summary data including fallback_results
        
    Returns:
        Path to the saved file
    """
    data_path = get_data_path()
    output_file = data_path / FALLBACK_SUMMARY_PATH
    
    # Ensure parent directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(summary_data, f, indent=2, default=str)
    
    logger.info(f"Saved fallback summary to {output_file}")
    return output_file

def check_fallback_threshold(summary_data: Dict[str, Any]) -> bool:
    """
    Check if the missing fraction after fallback exceeds the threshold.
    
    Args:
        summary_data: The complete summary data with fallback results
        
    Returns:
        True if missing fraction <= threshold (OK to continue), False otherwise
    """
    target_species = summary_data.get('target_species', [])
    missing_from_try = summary_data.get('missing_from_try', [])
    fallback_results = summary_data.get('fallback_results', {})
    
    if not target_species:
        logger.error("No target species found in summary data")
        return False
    
    # Count how many species still have no data after fallback
    still_missing = []
    for species in missing_from_try:
        # Check if this species has any fallback results with actual traits
        if species in fallback_results:
            result = fallback_results[species]
            # Check if we found any traits
            has_traits = False
            if result.get('phenoscape') and (result['phenoscape'].get('chemical_defenses') or 
                                              result['phenoscape'].get('physical_defenses')):
                has_traits = True
            # GBIF rarely provides actual traits, so we rely on Phenoscape
            if not has_traits and result.get('gbif'):
                # GBIF data is mostly verification, count as partial but not full trait data
                pass
            
            if not has_traits:
                still_missing.append(species)
        else:
            still_missing.append(species)
    
    missing_fraction = len(still_missing) / len(target_species) if target_species else 1.0
    
    logger.info(f"Fallback check: {len(still_missing)}/{len(target_species)} species still missing "
                f"({missing_fraction:.2%} missing fraction, threshold: {MISSING_THRESHOLD:.0%})")
    
    if missing_fraction > MISSING_THRESHOLD:
        logger.error(f"Missing fraction ({missing_fraction:.2%}) exceeds threshold ({MISSING_THRESHOLD:.0%})")
        return False
    
    return True

def main() -> int:
    """
    Main entry point for the fallback trait fetching pipeline.
    
    Returns:
        0 on success, 1 on failure
    """
    logger.info("Starting fallback trait data acquisition (T025b)")
    
    try:
        # Load input from T025a
        input_data = load_fallback_input()
        target_species = input_data['target_species']
        missing_from_try = input_data['missing_from_try']
        
        logger.info(f"Processing {len(missing_from_try)} species missing from TRY")
        
        if not missing_from_try:
            logger.info("No species missing from TRY, skipping fallback")
            return 0
        
        # Initialize or load existing summary
        data_path = get_data_path()
        summary_file = data_path / FALLBACK_SUMMARY_PATH
        
        if summary_file.exists():
            with open(summary_file, 'r') as f:
                summary_data = json.load(f)
        else:
            summary_data = {
                'target_species': target_species,
                'missing_from_try': missing_from_try,
                'fallback_results': {},
                'processed_at': datetime.utcnow().isoformat(),
                'source': 'phenoscape_gbif_fallback'
            }
        
        # Fetch traits for each missing species
        for species in missing_from_try:
            logger.info(f"Fetching fallback traits for: {species}")
            result = fetch_traits_for_species(species)
            summary_data['fallback_results'][species] = result
            
            # Save intermediate results periodically
            if len(summary_data['fallback_results']) % 5 == 0:
                save_trait_fallback_summary(summary_data)
        
        # Save final summary
        save_trait_fallback_summary(summary_data)
        
        # Check if we need to halt
        if not check_fallback_threshold(summary_data):
            # Write halt flag
            flag_file = data_path / "manifests" / "human_input_needed.flag"
            flag_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(flag_file, 'w') as f:
                f.write(json.dumps({
                    'reason': 'Trait data missing from both TRY and fallback sources',
                    'missing_fraction': len([s for s in missing_from_try 
                                             if s in summary_data['fallback_results'] and 
                                             not (summary_data['fallback_results'][s].get('phenoscape', {}).get('chemical_defenses') or
                                                  summary_data['fallback_results'][s].get('phenoscape', {}).get('physical_defenses'))]) / len(target_species),
                    'timestamp': datetime.utcnow().isoformat()
                }, indent=2))
            
            logger.error(f"Missing fraction exceeds threshold. Flag written to {flag_file}")
            raise SystemExit(1)
        
        logger.info("Fallback trait acquisition completed successfully")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Input file not found: {e}")
        return 1
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in input file: {e}")
        return 1
    except SystemExit:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in fallback trait acquisition: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
