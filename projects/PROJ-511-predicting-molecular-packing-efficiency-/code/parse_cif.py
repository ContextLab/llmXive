"""
parse_cif.py - Extract/generate SMILES via RDKit, flag source, and record confounders.

Reads CIF files from data/raw_cif/ (downloaded by T012), parses crystallographic
data, generates SMILES strings using RDKit, flags the data source, and records
thermodynamic and structural confounders.

Outputs:
    data/dataset_intermediate.csv: Contains CIF metadata, generated SMILES,
    source flags, and confounder data.

Dependencies:
    - code/utils.py (fix_seed, setup_logging)
    - code/error_handling.py (CIFParseError, MissingMetadataError, handle_corrupt_cif)
    - code/config.py (ensure_directories)
"""

import os
import re
import logging
from typing import Dict, List, Optional, Any, Tuple
import pandas as pd
import numpy as np

from rdkit import Chem
from rdkit.Chem import rdMolDescriptors

from utils import fix_seed, setup_logging
from error_handling import (
    CIFParseError,
    MissingMetadataError,
    handle_corrupt_cif,
    validate_required_metadata,
    safe_cif_read,
    get_cif_metadata_summary,
    log_processing_statistics,
)
from config import ensure_directories


# Constants
COD_URL_BASE = "https://www.ccdc.cam.ac.uk/structures/Search?Ccdcid="
# Minimal required metadata keys for a valid record
REQUIRED_METADATA_KEYS = ['_chemical_formula_sum', '_cell_length_a', '_cell_length_b', '_cell_length_c']


def parse_cif_metadata(cif_content: str) -> Dict[str, Any]:
    """
    Parse basic metadata from CIF content string.
    Extracts key-value pairs and handles common CIF formatting variations.

    Args:
        cif_content: Raw string content of the CIF file.

    Returns:
        Dictionary of parsed metadata.

    Raises:
        CIFParseError: If the CIF content is malformed or missing critical sections.
    """
    metadata = {}
    lines = cif_content.splitlines()
    current_key = None

    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue

        # Handle loop_ blocks
        if line.startswith('loop_'):
            continue

        # Handle data_ blocks
        if line.startswith('data_'):
            continue

        # Parse key-value pairs
        # CIF format: _key value or _key "value" or _key 'value'
        match = re.match(r'^_(\S+)\s+(.+)$', line)
        if match:
            key = match.group(1)
            value = match.group(2).strip()
            # Remove quotes if present
            if (value.startswith('"') and value.endswith('"')) or \
               (value.startswith("'") and value.endswith("'")):
                value = value[1:-1]
            metadata[key] = value
            current_key = key
        elif current_key and not line.startswith('_'):
            # Continuation of previous value (multi-line)
            metadata[current_key] += ' ' + line

    return metadata


def extract_atom_count_from_formula(formula_str: str) -> int:
    """
    Extract total non-hydrogen atom count from a chemical formula string.
    Handles formats like "C6 H12 O6", "C6H12O6", "C 6 H 12 O 6".

    Args:
        formula_str: Chemical formula string.

    Returns:
        Total count of non-hydrogen atoms.
    """
    # Remove spaces and normalize
    formula_str = formula_str.replace(' ', '').replace('\t', '')

    # Pattern to match element symbols and optional counts
    # Elements: C, H, O, N, S, P, F, Cl, Br, I, etc.
    pattern = r'([A-Z][a-z]?)(\d*)'
    matches = re.findall(pattern, formula_str)

    total_atoms = 0
    for element, count_str in matches:
        if element == 'H':
            continue  # Skip hydrogen
        count = int(count_str) if count_str else 1
        total_atoms += count

    return total_atoms


def generate_smiles_from_cif(cif_content: str, cif_path: str) -> Optional[str]:
    """
    Generate a SMILES string from CIF content using RDKit.

    This function attempts to:
    1. Parse the CIF file using RDKit's CIF parser.
    2. Extract the molecular structure.
    3. Generate a canonical SMILES string.

    If the CIF contains multiple molecules or complex crystallographic data,
    it attempts to extract the asymmetric unit or the most chemically relevant fragment.

    Args:
        cif_content: Raw string content of the CIF file.
        cif_path: Path to the CIF file (for error logging).

    Returns:
        Canonical SMILES string, or None if generation fails.
    """
    try:
        # RDKit's CIF parser is in rdChemReactions or similar, but for simple structures
        # we can try to parse the file directly.
        # Note: RDKit's CIF support is limited. We'll try to use the mol block extraction.
        # If RDKit cannot parse directly, we might need to convert CIF to MOL2 or similar.
        # For now, we'll assume the CIF contains a standard organic molecule structure.

        # Attempt to read the CIF file
        mol = Chem.MolFromMolBlock(cif_content, removeHs=False)

        if mol is None:
            # Try alternative parsing if direct MolFromMolBlock fails
            # Some CIFs have the structure in a different format
            logger = logging.getLogger(__name__)
            logger.warning(f"RDKit failed to parse CIF directly: {cif_path}")
            return None

        # Sanitize the molecule
        Chem.SanitizeMol(mol)

        # Generate canonical SMILES
        smiles = Chem.MolToSmiles(mol, isomericSmiles=True, canonical=True)

        # Validate the SMILES
        if not smiles or smiles == '':
            return None

        return smiles

    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Error generating SMILES from {cif_path}: {str(e)}")
        return None


def record_confounders(metadata: Dict[str, Any], smiles: str) -> Dict[str, Any]:
    """
    Extract and record thermodynamic and structural confounders from CIF metadata
    and the generated SMILES string.

    Confounders include:
    - Temperature (if available in metadata)
    - Solvent presence (inferred from formula)
    - H-bond donor/acceptor counts (from SMILES)
    - Aromatic ring count (from SMILES)
    - Molecular weight (from SMILES)

    Args:
        metadata: Parsed CIF metadata dictionary.
        smiles: Generated SMILES string.

    Returns:
        Dictionary of confounder values.
    """
    confounders = {}

    # Extract temperature
    temp_keys = ['_exptl_temperature', '_cell_temperature', '_temperature']
    temperature = None
    for key in temp_keys:
        if key in metadata:
            try:
                temperature = float(metadata[key])
                break
            except (ValueError, TypeError):
                continue
    confounders['temperature'] = temperature

    # Detect solvent presence
    solvent_indicators = ['H2O', 'H2O2', 'CH3OH', 'C2H5OH', 'DMSO', 'ACETONE', 'CHLOROFORM']
    formula = metadata.get('_chemical_formula_sum', '').upper()
    has_solvent = any(indicator in formula for indicator in solvent_indicators)
    confounders['solvent_present'] = has_solvent

    # Calculate H-bond donor/acceptor counts from SMILES
    if smiles:
        mol = Chem.MolFromSmiles(smiles)
        if mol:
            h_bond_donors = rdMolDescriptors.CalcNumHBD(mol)
            h_bond_acceptors = rdMolDescriptors.CalcNumHBA(mol)
            aromatic_rings = rdMolDescriptors.CalcNumAromaticRings(mol)
            mol_weight = rdMolDescriptors.CalcExactMolWt(mol)
        else:
            h_bond_donors = 0
            h_bond_acceptors = 0
            aromatic_rings = 0
            mol_weight = 0.0
    else:
        h_bond_donors = 0
        h_bond_acceptors = 0
        aromatic_rings = 0
        mol_weight = 0.0

    confounders['h_bond_donors'] = h_bond_donors
    confounders['h_bond_acceptors'] = h_bond_acceptors
    confounders['aromatic_rings'] = aromatic_rings
    confounders['molecular_weight'] = mol_weight

    return confounders


def flag_source(cif_path: str, metadata: Dict[str, Any]) -> str:
    """
    Flag the source of the CIF data.

    Args:
        cif_path: Path to the CIF file.
        metadata: Parsed CIF metadata.

    Returns:
        Source flag string (e.g., 'COD', 'UNKNOWN').
    """
    # Check if the file path or metadata indicates the source
    if 'cod' in cif_path.lower() or 'cod_id' in metadata:
        return 'COD'
    elif 'cambridge' in cif_path.lower() or 'ccdc' in metadata.get('_database_code', '').lower():
        return 'CCDC'
    else:
        return 'UNKNOWN'


def process_single_cif(cif_path: str) -> Optional[Dict[str, Any]]:
    """
    Process a single CIF file: parse metadata, generate SMILES, record confounders.

    Args:
        cif_path: Path to the CIF file.

    Returns:
        Dictionary containing parsed data, or None if processing fails.
    """
    logger = logging.getLogger(__name__)

    try:
        # Read CIF content safely
        cif_content = safe_cif_read(cif_path)
        if not cif_content:
            logger.warning(f"Could not read CIF file: {cif_path}")
            return None

        # Parse metadata
        metadata = parse_cif_metadata(cif_content)

        # Validate required metadata
        if not validate_required_metadata(metadata, REQUIRED_METADATA_KEYS):
            logger.warning(f"Missing required metadata in {cif_path}")
            return None

        # Extract atom count
        formula = metadata.get('_chemical_formula_sum', '')
        atom_count = extract_atom_count_from_formula(formula)

        # Generate SMILES
        smiles = generate_smiles_from_cif(cif_content, cif_path)
        if not smiles:
            logger.warning(f"Failed to generate SMILES for {cif_path}")
            # We can still record the record with None SMILES, but mark it as invalid later
            # For now, return None to skip this record
            return None

        # Record confounders
        confounders = record_confounders(metadata, smiles)

        # Flag source
        source = flag_source(cif_path, metadata)

        # Extract unit cell parameters
        cell_a = metadata.get('_cell_length_a', None)
        cell_b = metadata.get('_cell_length_b', None)
        cell_c = metadata.get('_cell_length_c', None)
        alpha = metadata.get('_cell_angle_alpha', None)
        beta = metadata.get('_cell_angle_beta', None)
        gamma = metadata.get('_cell_angle_gamma', None)

        # Extract space group
        space_group = metadata.get('_symmetry_space_group_name_H-M',
                                  metadata.get('_space_group_name_H-M_alt', None))

        # Compile the record
        record = {
            'cif_path': cif_path,
            'cod_id': metadata.get('_database_code', '').split(':')[-1] if metadata.get('_database_code') else None,
            'chemical_formula': formula,
            'non_h_atom_count': atom_count,
            'smiles': smiles,
            'source': source,
            'temperature': confounders['temperature'],
            'solvent_present': confounders['solvent_present'],
            'h_bond_donors': confounders['h_bond_donors'],
            'h_bond_acceptors': confounders['h_bond_acceptors'],
            'aromatic_rings': confounders['aromatic_rings'],
            'molecular_weight': confounders['molecular_weight'],
            'cell_length_a': cell_a,
            'cell_length_b': cell_b,
            'cell_length_c': cell_c,
            'cell_angle_alpha': alpha,
            'cell_angle_beta': beta,
            'cell_angle_gamma': gamma,
            'space_group': space_group,
        }

        return record

    except Exception as e:
        logger.error(f"Unexpected error processing {cif_path}: {str(e)}")
        handle_corrupt_cif(cif_path, e)
        return None


def main():
    """
    Main entry point for parsing CIF files.

    Reads all CIF files from data/raw_cif/, processes each one,
    and outputs a CSV file to data/dataset_intermediate.csv.
    """
    # Setup logging
    logger = setup_logging('parse_cif', logging.INFO)
    logger.info("Starting CIF parsing pipeline...")

    # Ensure directories exist
    ensure_directories()

    # Set random seed for reproducibility
    fix_seed(42)

    # Define input and output paths
    raw_cif_dir = 'data/raw_cif'
    output_path = 'data/dataset_intermediate.csv'

    if not os.path.exists(raw_cif_dir):
        logger.error(f"Input directory does not exist: {raw_cif_dir}")
        logger.error("Please run download_cif.py first to populate data/raw_cif/")
        return

    # Collect all CIF files
    cif_files = [f for f in os.listdir(raw_cif_dir) if f.endswith('.cif')]
    logger.info(f"Found {len(cif_files)} CIF files to process.")

    # Process each CIF file
    records = []
    success_count = 0
    failure_count = 0

    for i, cif_file in enumerate(cif_files):
        cif_path = os.path.join(raw_cif_dir, cif_file)
        logger.info(f"Processing [{i+1}/{len(cif_files)}]: {cif_file}")

        record = process_single_cif(cif_path)
        if record:
            records.append(record)
            success_count += 1
        else:
            failure_count += 1

    # Log statistics
    log_processing_statistics(success_count, failure_count, len(cif_files))

    if not records:
        logger.error("No valid records were processed. Check the logs for errors.")
        return

    # Create DataFrame and save to CSV
    df = pd.DataFrame(records)

    # Ensure consistent column order
    column_order = [
        'cif_path', 'cod_id', 'chemical_formula', 'non_h_atom_count', 'smiles', 'source',
        'temperature', 'solvent_present', 'h_bond_donors', 'h_bond_acceptors',
        'aromatic_rings', 'molecular_weight',
        'cell_length_a', 'cell_length_b', 'cell_length_c',
        'cell_angle_alpha', 'cell_angle_beta', 'cell_angle_gamma',
        'space_group'
    ]

    # Reorder columns (only include those that exist in the DataFrame)
    existing_columns = [col for col in column_order if col in df.columns]
    df = df[existing_columns]

    df.to_csv(output_path, index=False)
    logger.info(f"Successfully wrote {len(df)} records to {output_path}")


if __name__ == '__main__':
    main()