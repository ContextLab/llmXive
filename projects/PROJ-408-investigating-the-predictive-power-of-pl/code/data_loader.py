import logging
import time
import hashlib
import requests
import json
from typing import Dict, List, Optional, Tuple, Set, Any

# Configure logging for this module
logger = logging.getLogger(__name__)

class FetchResult:
    def __init__(self, data: Dict, checksum: str):
        self.data = data
        self.checksum = checksum

class SpeciesData:
    def __init__(self, ncbi_id: str, kegg_code: str, scientific_name: str):
        self.ncbi_id = ncbi_id
        self.kegg_code = kegg_code
        self.scientific_name = scientific_name

def calculate_sequence_checksum(fasta_content: str) -> str:
    """Calculates the SHA256 checksum of a FASTA string."""
    sha256_hash = hashlib.sha256()
    sha256_hash.update(fasta_content.encode('utf-8'))
    return sha256_hash.hexdigest()

def fetch_species_list_and_validate(species_list_path: str) -> List[SpeciesData]:
    """
    Fetches the species list from a file and validates the data.
    
    Performs explicit 1:1 mapping validation:
    1. Ensures every species has a valid, non-empty NCBI ID and KEGG code.
    2. Ensures NCBI IDs are unique across the list.
    3. Ensures KEGG codes are unique across the list.
    
    Raises:
        ValueError: If any ID is missing, empty, or not unique (ambiguous).
        FileNotFoundError: If the species list file does not exist.
    """
    species_list = []
    seen_ncbi_ids: Set[str] = set()
    seen_kegg_codes: Set[str] = set()
    
    try:
        with open(species_list_path, 'r') as f:
            lines = f.readlines()
    except FileNotFoundError:
        raise FileNotFoundError(f"Species list file not found: {species_list_path}")

    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            continue
        
        parts = line.split('\t')
        if len(parts) < 3:
            raise ValueError(f"Invalid line format at line {line_num}: expected 3 tab-separated columns, got {len(parts)}")
        
        ncbi_id, kegg_code, scientific_name = parts[0].strip(), parts[1].strip(), parts[2].strip()

        # Validation 1: Non-empty fields
        if not ncbi_id:
            raise ValueError(f"Empty NCBI ID at line {line_num} for species '{scientific_name}'")
        if not kegg_code:
            raise ValueError(f"Empty KEGG code at line {line_num} for species '{scientific_name}'")

        # Validation 2: Unique NCBI ID (1:1 mapping check)
        if ncbi_id in seen_ncbi_ids:
            raise ValueError(f"Ambiguous NCBI ID '{ncbi_id}' detected at line {line_num}. Each NCBI ID must appear exactly once.")
        seen_ncbi_ids.add(ncbi_id)

        # Validation 3: Unique KEGG code (1:1 mapping check)
        if kegg_code in seen_kegg_codes:
            raise ValueError(f"Ambiguous KEGG code '{kegg_code}' detected at line {line_num}. Each KEGG code must appear exactly once.")
        seen_kegg_codes.add(kegg_code)

        species_list.append(SpeciesData(ncbi_id, kegg_code, scientific_name))
    
    if not species_list:
        raise ValueError(f"No valid species found in {species_list_path}")

    logger.info(f"Successfully validated {len(species_list)} species mappings from {species_list_path}")
    return species_list

def fetch_marker_genes(species_id: str, loci: list) -> Dict:
    """Fetches marker genes for a given species."""
    # Placeholder for fetching marker genes
    # Replace with actual implementation
    return {"species_id": species_id, "loci": loci}

def fetch_metabolite_profiles(species_id: str) -> Dict:
    """Fetches metabolite profiles for a given species."""
    # Placeholder for fetching metabolite profiles
    # Replace with actual implementation
    return {"species_id": species_id, "metabolites": []}

def save_fasta_sequences(fasta_data: Dict, output_dir: str) -> None:
    """Saves FASTA sequences to a directory."""
    # Placeholder for saving FASTA sequences
    # Replace with actual implementation
    pass

def load_climate_data_from_usda(species_id: str) -> Dict:
    """Loads climate data from USDA."""
    # Placeholder for loading climate data
    # Replace with actual implementation
    return {}

def validate_and_fetch_all(species_list_path: str, loci: List[str]) -> Tuple[List[Dict], List[Dict]]:
    """Validates species mappings and fetches data."""
    # This function now relies on fetch_species_list_and_validate to perform
    # the strict 1:1 mapping validation before any fetching occurs.
    species_list = fetch_species_list_and_validate(species_list_path)
    
    # If we reach here, validation passed.
    marker_genes_data = [fetch_marker_genes(species.ncbi_id, loci) for species in species_list]
    metabolite_profiles_data = [fetch_metabolite_profiles(species.ncbi_id) for species in species_list]
    
    return marker_genes_data, metabolite_profiles_data
