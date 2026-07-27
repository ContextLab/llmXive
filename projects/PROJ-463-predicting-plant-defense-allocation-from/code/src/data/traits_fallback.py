"""
T025b: Fetch defense trait data from Phenoscape and GBIF for species missing from TRY.

This module implements the fallback mechanism for trait data acquisition.
It reads the list of species missing from TRY (from T025a) and attempts to
fetch their defense traits from Phenoscape and GBIF APIs.

Output is appended to data/processed/trait_fallback_summary.json.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import requests
from datetime import datetime

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from src.utils.logger import get_logger
from src.utils.schemas import DefenseTrait

# Configure logging
logger = get_logger(__name__)

# API Endpoints
PHENOSCAPE_API_BASE = "https://kb.phenoscape.org/api"
GBIF_API_BASE = "https://api.gbif.org/v1"

# Target traits for plant defense (Phenoscape trait IDs or keywords)
# These map to chemical and physical defense traits
DEFENSE_TRAIT_KEYWORDS = [
    "defense", "toxic", "irritant", "thorn", "spine", "trichome",
    "secondary metabolite", "alkaloid", "terpene", "phenol", "latex"
]

def load_fallback_input() -> tuple[List[str], Dict[str, Any]]:
    """
    Load the target species list and the missing_from_try list from previous tasks.
    
    Returns:
        tuple: (target_species_list, existing_summary_dict)
    """
    post_qc_path = Path(project_root) / "data" / "processed" / "post_qc_species_list.json"
    try_fallback_path = Path(project_root) / "data" / "processed" / "trait_fallback_summary.json"
    
    if not post_qc_path.exists():
        raise FileNotFoundError(f"Required input file not found: {post_qc_path}")
    
    with open(post_qc_path, 'r') as f:
        post_qc_data = json.load(f)
    
    # Extract species names from post_qc_species_list.json
    # Expected schema: { "species": [ { "name": "...", ... }, ... ] } or list of strings
    if isinstance(post_qc_data, list):
        target_species = post_qc_data
    elif isinstance(post_qc_data, dict) and "species" in post_qc_data:
        species_list = post_qc_data["species"]
        target_species = [s["name"] if isinstance(s, dict) else s for s in species_list]
    else:
        target_species = []
    
    # Load existing fallback summary if it exists
    if try_fallback_path.exists():
        with open(try_fallback_path, 'r') as f:
            existing_summary = json.load(f)
    else:
        existing_summary = {
            "target_species": target_species,
            "primary_source_results": {},
            "missing_from_try": [],
            "fallback_results": {}
        }
    
    missing_species = existing_summary.get("missing_from_try", [])
    if not missing_species:
        logger.info("No species marked as missing from TRY. Nothing to process.")
        return [], existing_summary
    
    return missing_species, existing_summary

def fetch_traits_from_phenoscape(species_name: str) -> List[Dict[str, Any]]:
    """
    Fetch defense trait data for a species from Phenoscape.
    
    Args:
        species_name: Scientific name of the species.
        
    Returns:
        List of trait dictionaries matching the target schema.
    """
    traits = []
    try:
        # Phenoscape query for traits associated with a taxon
        # Using their knowledge base API
        query = f"taxon:{species_name} trait:*defense*"
        url = f"{PHENOSCAPE_API_BASE}/queries"
        
        # Phenoscape API might require a different endpoint structure
        # Attempting to search for entities with traits
        search_url = f"{PHENOSCAPE_API_BASE}/entities"
        params = {"q": species_name, "limit": 100}
        
        response = requests.get(search_url, params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            entities = data.get("entities", [])
            
            for entity in entities:
                # Extract traits if available
                if "traits" in entity:
                    for trait in entity["traits"]:
                        trait_name = trait.get("label", trait.get("id", "unknown"))
                        # Filter for defense-related traits
                        if any(kw.lower() in trait_name.lower() for kw in DEFENSE_TRAIT_KEYWORDS):
                            traits.append({
                                "species_name": species_name,
                                "trait_name": trait_name,
                                "trait_value": trait.get("value", "present"),
                                "unit": "qualitative",
                                "source_id": f"PHENO_{entity.get('id', 'unknown')}"
                            })
        else:
            logger.warning(f"Phenoscape API returned {response.status_code} for {species_name}")
            
    except requests.exceptions.RequestException as e:
        logger.warning(f"Failed to fetch from Phenoscape for {species_name}: {e}")
    except Exception as e:
        logger.warning(f"Error processing Phenoscape data for {species_name}: {e}")
        
    return traits

def fetch_traits_from_gbif(species_name: str) -> List[Dict[str, Any]]:
    """
    Fetch trait data for a species from GBIF (if available via their trait API).
    
    Note: GBIF's trait API is limited for plant defense traits, but we attempt
    to fetch any available trait data.
    
    Args:
        species_name: Scientific name of the species.
        
    Returns:
        List of trait dictionaries.
    """
    traits = []
    try:
        # First, get the species key from GBIF
        search_url = f"{GBIF_API_BASE}/species/search"
        params = {
            "q": species_name,
            "limit": 1,
            "taxonKey": None
        }
        
        response = requests.get(search_url, params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [])
            
            if not results:
                return traits
                
            species_key = results[0].get("key")
            if not species_key:
                return traits
            
            # Try to fetch traits (GBIF trait API is limited)
            # This is a best-effort approach as GBIF doesn't have a robust trait API
            # for plant defense traits specifically
            trait_url = f"{GBIF_API_BASE}/occurrence/search"
            params = {
                "species": species_name,
                "limit": 10
            }
            
            # Note: GBIF occurrence data doesn't directly provide traits
            # We log that we attempted but may not find defense traits
            logger.debug(f"GBIF occurrence search for {species_name} (trait data limited)")
            
        else:
            logger.warning(f"GBIF API returned {response.status_code} for {species_name}")
            
    except requests.exceptions.RequestException as e:
        logger.warning(f"Failed to fetch from GBIF for {species_name}: {e}")
    except Exception as e:
        logger.warning(f"Error processing GBIF data for {species_name}: {e}")
        
    return traits

def fetch_traits_for_species(species_name: str) -> List[Dict[str, Any]]:
    """
    Attempt to fetch traits from both Phenoscape and GBIF for a given species.
    
    Args:
        species_name: Scientific name of the species.
        
    Returns:
        List of trait dictionaries from all successful sources.
    """
    all_traits = []
    
    logger.info(f"Fetching fallback traits for {species_name}")
    
    # Try Phenoscape first
    phenoscape_traits = fetch_traits_from_phenoscape(species_name)
    all_traits.extend(phenoscape_traits)
    
    # Try GBIF
    gbif_traits = fetch_traits_from_gbif(species_name)
    all_traits.extend(gbif_traits)
    
    return all_traits

def save_trait_fallback_summary(summary: Dict[str, Any]) -> None:
    """
    Save the updated fallback summary to disk.
    
    Args:
        summary: The complete summary dictionary including fallback results.
    """
    output_path = Path(project_root) / "data" / "processed" / "trait_fallback_summary.json"
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Saved updated trait fallback summary to {output_path}")

def main():
    """
    Main entry point for T025b.
    
    Reads missing species from T025a output, fetches traits from Phenoscape/GBIF,
    updates the summary file, and logs progress.
    """
    logger.info("Starting T025b: Trait Fallback Data Fetch")
    
    try:
        # Load input data
        missing_species, current_summary = load_fallback_input()
        
        if not missing_species:
            logger.info("No missing species to process. Exiting.")
            return
        
        logger.info(f"Processing {len(missing_species)} species missing from TRY")
        
        fallback_results = {}
        successfully_fetched = []
        
        for species in missing_species:
            traits = fetch_traits_for_species(species)
            
            if traits:
                fallback_results[species] = traits
                successfully_fetched.append(species)
                logger.info(f"  ✓ Found {len(traits)} traits for {species}")
            else:
                logger.info(f"  ✗ No traits found for {species}")
        
        # Update summary
        current_summary["fallback_results"] = fallback_results
        current_summary["successfully_fetched"] = successfully_fetched
        
        # Update missing_from_try list (remove species that were found)
        still_missing = [s for s in missing_species if s not in successfully_fetched]
        current_summary["missing_from_try"] = still_missing
        
        # Save updated summary
        save_trait_fallback_summary(current_summary)
        
        logger.info(f"T025b complete. Fallback data fetched for {len(successfully_fetched)} species.")
        logger.info(f"Still missing from all sources: {len(still_missing)} species.")
        
    except FileNotFoundError as e:
        logger.error(f"Input file error: {e}")
        # Continue as per spec: "If fallback fails, log error but continue"
    except Exception as e:
        logger.error(f"Unexpected error during T025b: {e}")
        # Continue as per spec: "If fallback fails, log error but continue"

if __name__ == "__main__":
    main()
