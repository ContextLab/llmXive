import logging
import time
import hashlib
import requests
import json
from typing import Dict, List, Optional, Tuple, Set, Any
from pathlib import Path
from dataclasses import dataclass, field

from config import get_config
from logging_config import get_logger

logger = get_logger(__name__)

@dataclass
class FetchResult:
    species_id: str
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

@dataclass
class SpeciesData:
    ncbi_id: str
    kegg_code: str
    scientific_name: str
    sequences: Dict[str, str] = field(default_factory=dict)
    metabolites: Set[str] = field(default_factory=set)
    has_sequence_data: bool = False
    has_metabolite_data: bool = False

def calculate_sequence_checksum(sequence: str) -> str:
    """Calculate SHA256 checksum for a DNA/protein sequence."""
    return hashlib.sha256(sequence.encode('utf-8')).hexdigest()

def _validate_species_mapping(species_list_path: Path) -> Dict[str, Tuple[str, str]]:
    """
    Validate 1:1 mapping between NCBI IDs and KEGG codes.
    
    Returns a dict: {scientific_name: (ncbi_id, kegg_code)}
    Raises ValueError if any mapping is ambiguous or missing.
    """
    if not species_list_path.exists():
        raise FileNotFoundError(f"Species list file not found: {species_list_path}")

    mapping = {}
    ncbi_to_kegg = {}
    kegg_to_ncbi = {}
    duplicates_ncbi = set()
    duplicates_kegg = set()
    missing_kegg = []
    missing_ncbi = []

    with open(species_list_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            parts = line.split('\t')
            if len(parts) < 3:
                raise ValueError(f"Line {line_num}: Invalid format. Expected 'NCBI_ID\\tKEGG_CODE\\tScientificName', got: {line}")

            ncbi_id, kegg_code, scientific_name = parts[0].strip(), parts[1].strip(), parts[2].strip()

            if not ncbi_id:
                missing_ncbi.append((line_num, scientific_name))
            if not kegg_code:
                missing_kegg.append((line_num, scientific_name))

            # Check for duplicates in NCBI ID mapping
            if ncbi_id in ncbi_to_kegg:
                if ncbi_to_kegg[ncbi_id] != kegg_code:
                    duplicates_ncbi.add(ncbi_id)
            else:
                ncbi_to_kegg[ncbi_id] = kegg_code

            # Check for duplicates in KEGG code mapping
            if kegg_code in kegg_to_ncbi:
                if kegg_to_ncbi[kegg_code] != ncbi_id:
                    duplicates_kegg.add(kegg_code)
            else:
                kegg_to_ncbi[kegg_code] = ncbi_id

            mapping[scientific_name] = (ncbi_id, kegg_code)

    error_messages = []

    if missing_ncbi:
        error_messages.append(f"Found {len(missing_ncbi)} entries with missing NCBI IDs:")
        for line_num, name in missing_ncbi[:5]:
            error_messages.append(f"  Line {line_num}: {name}")

    if missing_kegg:
        error_messages.append(f"Found {len(missing_kegg)} entries with missing KEGG codes:")
        for line_num, name in missing_kegg[:5]:
            error_messages.append(f"  Line {line_num}: {name}")

    if duplicates_ncbi:
        error_messages.append(f"Found ambiguous NCBI ID mappings (one NCBI ID maps to multiple KEGG codes): {duplicates_ncbi}")

    if duplicates_kegg:
        error_messages.append(f"Found ambiguous KEGG code mappings (one KEGG code maps to multiple NCBI IDs): {duplicates_kegg}")

    if error_messages:
        full_error = "\n".join(error_messages)
        logger.error(f"Species ID mapping validation failed:\n{full_error}")
        raise ValueError(f"Species ID mapping validation failed. {full_error}")

    logger.info(f"Species ID mapping validation passed for {len(mapping)} species.")
    return mapping

def fetch_species_list_and_validate(species_list_path: str) -> Dict[str, Tuple[str, str]]:
    """
    Load and validate the species list from file.
    Ensures 1:1 mapping between NCBI IDs and KEGG codes before any fetches.
    
    Args:
        species_list_path: Path to the species list file (data/raw/species_list.txt)
        
    Returns:
        Dict mapping scientific_name -> (ncbi_id, kegg_code)
        
    Raises:
        ValueError: If mapping is ambiguous or missing
        FileNotFoundError: If species list file doesn't exist
    """
    path = Path(species_list_path)
    return _validate_species_mapping(path)

def fetch_marker_genes(species_id: str, loci: List[str]) -> FetchResult:
    """
    Fetch marker genes for a species using NCBI Entrez.
    
    Args:
        species_id: NCBI Taxonomy ID
        loci: List of gene markers to fetch (e.g., ['18S', 'rbcL', 'matK'])
        
    Returns:
        FetchResult with sequences or error details
    """
    config = get_config()
    email = config.get('ncbi_email', 'llmXive@example.com')
    api_key = config.get('ncbi_api_key')

    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    sequences = {}

    for locus in loci:
        try:
            # Search for sequences
            params = {
                'db': 'nuccore',
                'term': f"{species_id}[Organism] AND {locus}[Gene] AND biomol_mrna[Properties]",
                'retmode': 'json',
                'retmax': 1
            }
            if api_key:
                params['api_key'] = api_key

            response = requests.get(base_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            if 'esearchresult' not in data or not data['esearchresult'].get('idlist'):
                logger.warning(f"Species {species_id} ({locus}): No sequences found")
                continue

            seq_id = data['esearchresult']['idlist'][0]

            # Fetch sequence
            fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
            fetch_params = {
                'db': 'nuccore',
                'id': seq_id,
                'rettype': 'fasta',
                'retmode': 'text'
            }
            if api_key:
                fetch_params['api_key'] = api_key

            seq_response = requests.get(fetch_url, params=fetch_params, timeout=30)
            seq_response.raise_for_status()
            seq_text = seq_response.text

            # Parse FASTA (simple extraction)
            seq_lines = seq_text.split('\n')
            seq_body = ''.join(line for line in seq_lines if not line.startswith('>'))
            sequences[locus] = seq_body

            time.sleep(0.34)  # NCBI rate limit

        except Exception as e:
            logger.error(f"Species {species_id} ({locus}): Fetch failed - {str(e)}")
            continue

    if not sequences:
        return FetchResult(
            species_id=species_id,
            success=False,
            error=f"No sequences found for any of the requested loci: {loci}"
        )

    return FetchResult(
        species_id=species_id,
        success=True,
        data={'sequences': sequences}
    )

def fetch_metabolite_profiles(species_id: str, kegg_code: str) -> FetchResult:
    """
    Fetch metabolite profiles for a species using KEGG API.
    
    Args:
        species_id: NCBI Taxonomy ID (for logging)
        kegg_code: KEGG organism code
        
    Returns:
        FetchResult with metabolite set or error details
    """
    if not kegg_code:
        return FetchResult(
            species_id=species_id,
            success=False,
            error="KEGG code is missing for this species"
        )

    try:
        # Fetch compound list for organism
        url = f"https://rest.kegg.jp/list/compound/{kegg_code}"
        response = requests.get(url, timeout=30)
        
        if response.status_code == 404:
            logger.warning(f"Species {species_id} ({kegg_code}): No KEGG entry found")
            return FetchResult(
                species_id=species_id,
                success=False,
                error=f"No KEGG entry found for organism code: {kegg_code}"
            )
        
        response.raise_for_status()
        
        metabolites = set()
        for line in response.text.strip().split('\n'):
            if line:
                parts = line.split('\t')
                if parts:
                    compound_id = parts[0]
                    metabolites.add(compound_id)

        if not metabolites:
            logger.warning(f"Species {species_id} ({kegg_code}): No metabolites found")
            return FetchResult(
                species_id=species_id,
                success=False,
                error=f"No metabolites found for organism code: {kegg_code}"
            )

        return FetchResult(
            species_id=species_id,
            success=True,
            data={'metabolites': metabolites}
        )

    except Exception as e:
        logger.error(f"Species {species_id} ({kegg_code}): Fetch failed - {str(e)}")
        return FetchResult(
            species_id=species_id,
            success=False,
            error=str(e)
        )

def save_fasta_sequences(sequences: Dict[str, str], output_path: Path, species_id: str) -> None:
    """Save fetched sequences to a FASTA file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for locus, seq in sequences.items():
            f.write(f">{species_id}_{locus}\n")
            # Wrap lines at 80 chars
            for i in range(0, len(seq), 80):
                f.write(seq[i:i+80] + '\n')

    logger.info(f"Saved sequences for {species_id} to {output_path}")

def load_climate_data_from_usda(species_list: List[Tuple[str, str, str]]) -> Dict[str, Dict[str, float]]:
    """
    Load climate data from USDA PLANTS database.
    Note: This is a placeholder for the actual implementation which would
    fetch from USDA PLANTS API or a verified data source.
    """
    # In a real implementation, this would fetch from USDA PLANTS
    # For now, return empty dict to indicate no data
    logger.warning("USDA climate data fetch not yet implemented")
    return {}

def validate_and_fetch_all(species_list_path: str, loci: List[str]) -> Tuple[Dict[str, SpeciesData], Dict[str, str]]:
    """
    Validate species mappings and fetch all data for valid species.
    
    Args:
        species_list_path: Path to species list file
        loci: List of loci to fetch
        
    Returns:
        Tuple of (species_data_dict, errors_dict)
    """
    # Step 1: Validate mappings (CRITICAL - T039)
    try:
        mapping = fetch_species_list_and_validate(species_list_path)
    except (ValueError, FileNotFoundError) as e:
        logger.critical(f"Species mapping validation failed: {str(e)}")
        raise

    species_data = {}
    errors = {}

    for scientific_name, (ncbi_id, kegg_code) in mapping.items():
        logger.info(f"Processing {scientific_name} (NCBI: {ncbi_id}, KEGG: {kegg_code})")
        
        # Fetch sequences
        seq_result = fetch_marker_genes(ncbi_id, loci)
        
        # Fetch metabolites
        metab_result = fetch_metabolite_profiles(ncbi_id, kegg_code)
        
        has_seq = seq_result.success
        has_met = metab_result.success

        if not has_seq and not has_met:
            errors[scientific_name] = "Missing both sequence and metabolite data"
            continue

        if not has_seq:
            logger.warning(f"{scientific_name}: Missing sequence data, excluding from phylogeny")
        if not has_met:
            logger.warning(f"{scientific_name}: Missing metabolite data, excluding from matrix")

        species_data[scientific_name] = SpeciesData(
            ncbi_id=ncbi_id,
            kegg_code=kegg_code,
            scientific_name=scientific_name,
            sequences=seq_result.data.get('sequences', {}) if has_seq else {},
            metabolites=metab_result.data.get('metabolites', set()) if has_met else set(),
            has_sequence_data=has_seq,
            has_metabolite_data=has_met
        )

    return species_data, errors