"""
Fallback trait data acquisition from Phenoscape and GBIF.

This module implements T025b: fetching defense trait data from secondary sources
(Phenoscape, GBIF) when primary TRY database data is missing.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import requests

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.logger import get_logger

# Configure logging
logger = get_logger(__name__)

# Constants
PHENOSCAPE_API_BASE = "https://phenoscape.org/api"
GBIF_API_BASE = "https://api.gbif.org/v1"
FALLBACK_SUMMARY_PATH = Path("data/processed/trait_fallback_summary.json")
POST_QC_SPECIES_PATH = Path("data/processed/post_qc_species_list.json")


def load_fallback_input() -> Dict[str, Any]:
    """
    Load the input data for fallback trait acquisition.

    Reads:
    1. Target species list from data/processed/post_qc_species_list.json
    2. Missing species list from data/processed/trait_fallback_summary.json (missing_from_try)

    Returns:
        Dict containing target_species and missing_from_try lists.
    """
    # Load target species list
    if not POST_QC_SPECIES_PATH.exists():
        raise FileNotFoundError(
            f"Required input file not found: {POST_QC_SPECIES_PATH}. "
            "Run T014 (QC) first to generate this file."
        )

    with open(POST_QC_SPECIES_PATH, 'r') as f:
        post_qc_data = json.load(f)

    target_species = [item['name'] for item in post_qc_data.get('species', [])]

    if not target_species:
        raise ValueError("No target species found in post_qc_species_list.json")

    logger.info(f"Loaded {len(target_species)} target species from QC results")

    # Load missing_from_try list from T025a output
    missing_from_try = []
    if FALLBACK_SUMMARY_PATH.exists():
        with open(FALLBACK_SUMMARY_PATH, 'r') as f:
            fallback_data = json.load(f)
            missing_from_try = fallback_data.get('missing_from_try', [])
            logger.info(f"Loaded {len(missing_from_try)} species missing from TRY")
    else:
        logger.warning(f"Fallback summary not found at {FALLBACK_SUMMARY_PATH}. "
                     "Proceeding with all target species as missing from TRY.")
        missing_from_try = target_species

    return {
        'target_species': target_species,
        'missing_from_try': missing_from_try
    }


def fetch_traits_from_phenoscape(species_name: str) -> Optional[Dict[str, Any]]:
    """
    Fetch defense trait data for a species from Phenoscape API.

    Phenoscape KB contains phenotype data linked to taxa. We search for
    traits related to defense (e.g., trichomes, chemical defenses).

    Args:
        species_name: Scientific name of the species (e.g., "Arabidopsis thaliana")

    Returns:
        Dict containing trait data if found, None otherwise.
    """
    try:
        # Normalize species name for API query
        # Phenoscape uses taxon IDs, so we first need to resolve the name
        taxon_search_url = f"{PHENOSCAPE_API_BASE}/taxon/search"
        params = {'q': species_name, 'limit': 1}

        logger.debug(f"Querying Phenoscape for taxon: {species_name}")
        response = requests.get(taxon_search_url, params=params, timeout=10)

        if response.status_code != 200:
            logger.warning(f"Phenoscape taxon search failed for {species_name}: "
                         f"HTTP {response.status_code}")
            return None

        taxon_data = response.json()
        if not taxon_data or 'results' not in taxon_data or len(taxon_data['results']) == 0:
            logger.debug(f"No Phenoscape taxon found for {species_name}")
            return None

        # Get the first matching taxon ID
        taxon_id = taxon_data['results'][0].get('id')
        if not taxon_id:
            return None

        # Fetch phenotype/trait data for this taxon
        phenotype_url = f"{PHENOSCAPE_API_BASE}/taxon/{taxon_id}/phenotypes"
        response = requests.get(phenotype_url, timeout=10)

        if response.status_code != 200:
            logger.warning(f"Phenoscape phenotype fetch failed for {species_name}: "
                         f"HTTP {response.status_code}")
            return None

        phenotype_data = response.json()

        # Filter for defense-related traits
        # Phenoscape uses ontologies; we look for traits related to defense
        defense_keywords = ['defense', 'trichome', 'hair', 'chemical', 'toxin',
                          'secondary metabolite', 'herbivore', 'resistance']

        traits = []
        if 'phenotypes' in phenotype_data:
            for p in phenotype_data['phenotypes']:
                label = p.get('label', '').lower()
                # Simple keyword matching for defense traits
                if any(kw in label for kw in defense_keywords):
                    traits.append({
                        'trait_name': p.get('label'),
                        'value': p.get('value'),
                        'source': 'phenoscape',
                        'ontology_term': p.get('term', {}).get('id') if 'term' in p else None
                    })

        if traits:
            logger.info(f"Found {len(traits)} defense traits for {species_name} in Phenoscape")
            return {
                'species': species_name,
                'traits': traits,
                'source': 'phenoscape'
            }
        else:
            logger.debug(f"No defense traits found for {species_name} in Phenoscape")
            return None

    except requests.exceptions.RequestException as e:
        logger.error(f"Phenoscape API request failed for {species_name}: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching Phenoscape traits for {species_name}: {str(e)}")
        return None


def fetch_traits_from_gbif(species_name: str) -> Optional[Dict[str, Any]]:
    """
    Fetch trait/occurrence data for a species from GBIF API.

    GBIF primarily provides occurrence data, but we can extract
    morphological traits from the associated measurements when available.

    Args:
        species_name: Scientific name of the species

    Returns:
        Dict containing trait data if found, None otherwise.
    """
    try:
        # GBIF uses scientificName parameter for species search
        occurrence_url = f"{GBIF_API_BASE}/occurrence/search"
        params = {
            'scientificName': species_name,
            'limit': 50,  # Sample size for trait extraction
            'hasCoordinate': True
        }

        logger.debug(f"Querying GBIF for occurrences: {species_name}")
        response = requests.get(occurrence_url, params=params, timeout=10)

        if response.status_code != 200:
            logger.warning(f"GBIF occurrence search failed for {species_name}: "
                         f"HTTP {response.status_code}")
            return None

        occurrence_data = response.json()
        results = occurrence_data.get('results', [])

        if not results:
            logger.debug(f"No GBIF occurrences found for {species_name}")
            return None

        # Extract traits from occurrence measurements
        # GBIF occurrences may have 'extensions' with morphological data
        traits = []
        defense_traits_found = 0

        for occ in results:
            # Check for measurementOrFact extension (contains trait data)
            extensions = occ.get('extensions', {})
            for ext_key, ext_data in extensions.items():
                if 'measurement' in ext_key.lower() or 'fact' in ext_key.lower():
                    for item in ext_data.get('values', []):
                        measurement_type = item.get('type', '').lower()
                        # Look for defense-related measurements
                        if any(kw in measurement_type for kw in ['defense', 'hair', 'trichome', 'chemical', 'toxin']):
                            traits.append({
                                'trait_name': item.get('type'),
                                'value': item.get('value'),
                                'unit': item.get('unit'),
                                'source': 'gbif',
                                'occurrence_id': occ.get('key')
                            })
                            defense_traits_found += 1

        if traits:
            logger.info(f"Found {len(traits)} defense traits for {species_name} in GBIF")
            return {
                'species': species_name,
                'traits': traits,
                'source': 'gbif'
            }
        else:
            logger.debug(f"No defense traits found for {species_name} in GBIF")
            return None

    except requests.exceptions.RequestException as e:
        logger.error(f"GBIF API request failed for {species_name}: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching GBIF traits for {species_name}: {str(e)}")
        return None


def fetch_traits_for_species(species_name: str) -> Optional[Dict[str, Any]]:
    """
    Attempt to fetch traits for a species from fallback sources.

    Tries Phenoscape first, then GBIF. Returns the first successful result.

    Args:
        species_name: Scientific name of the species

    Returns:
        Dict with traits if found from any source, None otherwise.
    """
    logger.info(f"Attempting fallback trait fetch for: {species_name}")

    # Try Phenoscape first
    phenoscape_traits = fetch_traits_from_phenoscape(species_name)
    if phenoscape_traits:
        return phenoscape_traits

    # Try GBIF
    gbif_traits = fetch_traits_from_gbif(species_name)
    if gbif_traits:
        return gbif_traits

    logger.info(f"No fallback traits found for {species_name}")
    return None


def save_trait_fallback_summary(summary: Dict[str, Any]) -> None:
    """
    Save the updated trait fallback summary to disk.

    Args:
        summary: Complete summary dict including fallback_results and updated missing lists.
    """
    # Ensure output directory exists
    FALLBACK_SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(FALLBACK_SUMMARY_PATH, 'w') as f:
        json.dump(summary, f, indent=2)

    logger.info(f"Saved trait fallback summary to {FALLBACK_SUMMARY_PATH}")


def main() -> int:
    """
    Main entry point for T025b: Fallback trait data acquisition.

    Reads missing species from T025a output, fetches traits from
    Phenoscape and GBIF, and updates the trait fallback summary.

    Returns:
        0 on success, 1 on failure.
    """
    logger.info("Starting T025b: Fallback trait data acquisition")

    try:
        # Load input data
        input_data = load_fallback_input()
        missing_from_try = input_data['missing_from_try']
        target_species = input_data['target_species']

        if not missing_from_try:
            logger.info("No species missing from TRY. Skipping fallback fetch.")
            return 0

        logger.info(f"Fetching fallback traits for {len(missing_from_try)} species")

        # Load existing summary or initialize
        fallback_results = {}
        updated_missing_from_try = []

        if FALLBACK_SUMMARY_PATH.exists():
            with open(FALLBACK_SUMMARY_PATH, 'r') as f:
                existing_summary = json.load(f)
                fallback_results = existing_summary.get('fallback_results', {})
        else:
            # Initialize summary structure
            existing_summary = {
                'target_species': target_species,
                'primary_source_results': {},
                'missing_from_try': missing_from_try,
                'fallback_results': {},
                'missing_from_all_sources': []
            }

        # Fetch traits for each missing species
        found_count = 0
        for species in missing_from_try:
            traits_data = fetch_traits_for_species(species)

            if traits_data:
                fallback_results[species] = traits_data
                found_count += 1
                logger.info(f"Successfully fetched fallback traits for {species}")
            else:
                updated_missing_from_try.append(species)
                logger.warning(f"Failed to fetch fallback traits for {species}")

        # Update the summary
        existing_summary['fallback_results'] = fallback_results
        existing_summary['missing_from_try'] = updated_missing_from_try
        existing_summary['missing_from_all_sources'] = updated_missing_from_try
        existing_summary['fallback_stats'] = {
            'total_missing_from_try': len(missing_from_try),
            'found_in_fallback': found_count,
            'still_missing': len(updated_missing_from_try)
        }

        # Save updated summary
        save_trait_fallback_summary(existing_summary)

        logger.info(f"T025b complete: Found fallback traits for {found_count}/{len(missing_from_try)} species")
        return 0

    except FileNotFoundError as e:
        logger.error(f"Input file error: {str(e)}")
        return 1
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {str(e)}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error in T025b: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())
