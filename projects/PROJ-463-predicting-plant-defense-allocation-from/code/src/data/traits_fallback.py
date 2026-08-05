"""
Traits Fallback Module for Phenoscape and GBIF.

This module implements the fallback logic for fetching defense trait data
when primary TRY database sources are unavailable or missing data for specific species.
"""

import os
import sys
import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Import from local project structure
from src.utils.config import get_data_path
from src.utils.logger import get_logger

# Initialize logger
logger = get_logger(__name__)

# Constants
PHENOSCAPE_API_BASE = "https://api.phenoscape.org/v3"
GBIF_API_BASE = "https://api.gbif.org/v2"
DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3
BACKOFF_FACTOR = 1.0

def create_retry_session() -> requests.Session:
    """Create a requests session with retry logic."""
    session = requests.Session()
    retry = Retry(
        total=MAX_RETRIES,
        backoff_factor=BACKOFF_FACTOR,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST"]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def load_fallback_input() -> Dict[str, Any]:
    """
    Load input data from T014 and T025a outputs.

    Returns:
        Dict containing target species list and missing_from_try list.
    """
    data_path = get_data_path()
    qc_list_path = Path(data_path) / "processed" / "post_qc_species_list.json"
    try_summary_path = Path(data_path) / "processed" / "trait_fallback_summary.json"

    # Load target species list from T014
    if not qc_list_path.exists():
        raise FileNotFoundError(
            f"Target species list not found at {qc_list_path}. "
            "Ensure T014 (post_qc_species_list.json) has been completed."
        )

    with open(qc_list_path, 'r', encoding='utf-8') as f:
        qc_data = json.load(f)

    # Extract species names from the list
    target_species = [item['species'] for item in qc_data.get('included', [])]

    # Load existing trait fallback summary from T025a
    if try_summary_path.exists():
        with open(try_summary_path, 'r', encoding='utf-8') as f:
            try_data = json.load(f)
        missing_from_try = try_data.get('missing_from_try', [])
    else:
        # If T025a hasn't run, assume all target species are missing
        missing_from_try = target_species
        logger.warning(
            f"Trait fallback summary not found at {try_summary_path}. "
            f"Assuming all {len(target_species)} species are missing from TRY."
        )

    return {
        'target_species': target_species,
        'missing_from_try': missing_from_try,
        'existing_summary': try_data if try_summary_path.exists() else None
    }

def fetch_traits_from_phenoscape(session: requests.Session, species_name: str) -> Optional[Dict[str, Any]]:
    """
    Fetch defense trait data from Phenoscape API.

    Args:
        session: Retry-enabled requests session.
        species_name: Scientific name of the species.

    Returns:
        Dict of trait data or None if not found.
    """
    try:
        # Phenoscape taxon search
        taxon_search_url = f"{PHENOSCAPE_API_BASE}/taxon/search"
        params = {'q': species_name}

        logger.debug(f"Searching Phenoscape for {species_name}")
        response = session.get(taxon_search_url, params=params, timeout=DEFAULT_TIMEOUT)

        if response.status_code != 200:
            logger.warning(f"Phenoscape taxon search failed for {species_name}: {response.status_code}")
            return None

        taxon_data = response.json()
        if not taxon_data.get('results'):
            logger.debug(f"No Phenoscape taxon match for {species_name}")
            return None

        # Get the first matching taxon ID
        taxon_id = taxon_data['results'][0].get('id')
        if not taxon_id:
            return None

        # Fetch phenotypic data for this taxon
        phenotypes_url = f"{PHENOSCAPE_API_BASE}/taxon/{taxon_id}/phenotypes"
        response = session.get(phenotypes_url, timeout=DEFAULT_TIMEOUT)

        if response.status_code != 200:
            logger.warning(f"Phenoscape phenotype fetch failed for {species_name}: {response.status_code}")
            return None

        phenotype_data = response.json()

        # Extract relevant defense traits (simplified mapping)
        traits = {}
        for phen in phenotype_data.get('phenotypes', []):
            entity = phen.get('entity', {})
            quality = phen.get('quality', {})

            # Look for defense-related terms
            entity_label = entity.get('label', '').lower()
            quality_label = quality.get('label', '').lower() if quality else ''

            if any(term in entity_label for term in ['spine', 'trichome', 'thorn', 'gland', 'chemical', 'toxin']):
                trait_key = f"phenoscape_{entity_label.replace(' ', '_')}"
                traits[trait_key] = {
                    'value': 1.0,  # Presence indicator
                    'unit': 'presence',
                    'source': 'phenoscape',
                    'confidence': 0.8
                }

        return traits if traits else None

    except requests.RequestException as e:
        logger.error(f"Phenoscape API error for {species_name}: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching Phenoscape data for {species_name}: {str(e)}")
        return None

def fetch_traits_from_gbif(session: requests.Session, species_name: str) -> Optional[Dict[str, Any]]:
    """
    Fetch defense trait data from GBIF API.

    Note: GBIF primarily provides occurrence data, but we can infer some
    trait information from associated literature or linked datasets.
    This is a simplified implementation as GBIF is not a primary trait database.

    Args:
        session: Retry-enabled requests session.
        species_name: Scientific name of the species.

    Returns:
        Dict of trait data or None if not found.
    """
    try:
        # GBIF species search
        search_url = f"{GBIF_API_BASE}/species/search"
        params = {
            'q': species_name,
            'limit': 1
        }

        logger.debug(f"Searching GBIF for {species_name}")
        response = session.get(search_url, params=params, timeout=DEFAULT_TIMEOUT)

        if response.status_code != 200:
            logger.warning(f"GBIF species search failed for {species_name}: {response.status_code}")
            return None

        search_data = response.json()
        if not search_data.get('results'):
            logger.debug(f"No GBIF species match for {species_name}")
            return None

        gbif_key = search_data['results'][0].get('key')
        if not gbif_key:
            return None

        # Fetch occurrence data as a proxy for trait availability
        occurrence_url = f"{GBIF_API_BASE}/occurrence/search"
        params = {
            'species': species_name,
            'limit': 10,
            'hasCoordinate': True
        }

        response = session.get(occurrence_url, params=params, timeout=DEFAULT_TIMEOUT)

        if response.status_code != 200:
            logger.warning(f"GBIF occurrence fetch failed for {species_name}: {response.status_code}")
            return None

        occurrence_data = response.json()
        total_count = occurrence_data.get('count', 0)

        # Create a proxy trait indicating data availability
        traits = {
            'gbif_occurrence_count': {
                'value': float(total_count),
                'unit': 'occurrences',
                'source': 'gbif',
                'confidence': 0.5,
                'note': 'GBIF occurrence data as proxy for trait availability'
            }
        }

        return traits

    except requests.RequestException as e:
        logger.error(f"GBIF API error for {species_name}: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching GBIF data for {species_name}: {str(e)}")
        return None

def fetch_traits_for_species(
    session: requests.Session,
    species_name: str,
    try_api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Fetch traits for a single species from fallback sources.

    Args:
        session: Retry-enabled requests session.
        species_name: Scientific name of the species.
        try_api_key: Optional TRY API key (not used in fallback, but kept for signature consistency).

    Returns:
        Dict containing results from Phenoscape and GBIF.
    """
    phenoscape_traits = fetch_traits_from_phenoscape(session, species_name)
    gbif_traits = fetch_traits_from_gbif(session, species_name)

    return {
        'species': species_name,
        'phenoscape': phenoscape_traits,
        'gbif': gbif_traits,
        'found_any': any([phenoscape_traits, gbif_traits])
    }

def save_trait_fallback_summary(
    summary_data: Dict[str, Any],
    output_path: Path
) -> None:
    """
    Save the trait fallback summary to JSON.

    Args:
        summary_data: The complete summary dictionary.
        output_path: Path to save the JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(summary_data, f, indent=2, default=str)
    logger.info(f"Saved trait fallback summary to {output_path}")

def main():
    """
    Main entry point for the trait fallback task.

    This function:
    1. Loads target species from T014 output.
    2. Loads missing species list from T025a output.
    3. Fetches traits from Phenoscape and GBIF for missing species.
    4. Updates the trait fallback summary with results.
    5. Writes the updated summary to disk.
    """
    logger.info("Starting trait fallback task (T025b)")

    try:
        # Load input data
        input_data = load_fallback_input()
        target_species = input_data['target_species']
        missing_from_try = input_data['missing_from_try']
        existing_summary = input_data['existing_summary']

        logger.info(f"Processing {len(missing_from_try)} species missing from TRY")
        logger.info(f"Target species list contains {len(target_species)} species")

        # Create retry-enabled session
        session = create_retry_session()

        # Initialize or load summary structure
        if existing_summary:
            summary = existing_summary
            if 'fallback_results' not in summary:
                summary['fallback_results'] = {}
            if 'missing_from_try' not in summary:
                summary['missing_from_try'] = missing_from_try
        else:
            summary = {
                'target_species': target_species,
                'primary_source_results': {},
                'missing_from_try': missing_from_try,
                'fallback_results': {},
                'missing_from_all_sources': []
            }

        # Track species that were successfully found in fallback
        found_in_fallback = []

        # Process each missing species
        for species in missing_from_try:
            logger.info(f"Fetching fallback traits for: {species}")

            # Fetch from Phenoscape and GBIF
            result = fetch_traits_for_species(session, species)

            # Store results
            if result['found_any']:
                summary['fallback_results'][species] = {
                    'phenoscape': result['phenoscape'],
                    'gbif': result['gbif']
                }
                found_in_fallback.append(species)
                logger.info(f"  ✓ Found traits for {species} in fallback sources")
            else:
                logger.warning(f"  ✗ No traits found for {species} in fallback sources")

            # Rate limiting
            time.sleep(0.5)

        # Update missing_from_try list (remove species found in fallback)
        summary['missing_from_try'] = [
            s for s in summary['missing_from_try'] if s not in found_in_fallback
        ]

        # Update missing_from_all_sources list
        summary['missing_from_all_sources'] = summary['missing_from_try']

        # Save results
        data_path = get_data_path()
        output_path = Path(data_path) / "processed" / "trait_fallback_summary.json"
        save_trait_fallback_summary(summary, output_path)

        logger.info(f"Trait fallback complete. Found traits for {len(found_in_fallback)} species.")
        logger.info(f"Remaining missing from all sources: {len(summary['missing_from_all_sources'])}")

        return summary

    except FileNotFoundError as e:
        logger.error(f"Input file not found: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error in trait fallback task: {str(e)}")
        raise

if __name__ == "__main__":
    main()
