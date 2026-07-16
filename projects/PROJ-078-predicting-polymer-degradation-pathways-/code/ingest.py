from __future__ import annotations

import logging
from typing import List, Dict, Any, Optional

from rdkit import Chem
from rdkit.Chem import rdchem

from data_models import MolecularGraph
from utils import get_logger, with_exponential_backoff

logger = get_logger(__name__)

def validate_smiles(smiles: str) -> bool:
    """Validate if a SMILES string is chemically valid using RDKit."""
    if not smiles or not isinstance(smiles, str):
        logger.warning(f"Invalid SMILES input: {smiles} (type: {type(smiles)})")
        return False
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            logger.warning(f"RDKit failed to parse SMILES: {smiles}")
            return False
        return True
    except Exception as e:
        logger.error(f"Exception during SMILES validation for '{smiles}': {e}")
        return False

def smiles_to_molecular_graph(smiles: str) -> Optional[MolecularGraph]:
    """Convert a valid SMILES string to a MolecularGraph data object."""
    if not validate_smiles(smiles):
        logger.debug(f"Skipping graph conversion for invalid SMILES: {smiles}")
        return None
    try:
        mol = Chem.MolFromSmiles(smiles)
        # Basic atom and bond extraction for graph representation
        atoms = []
        for atom in mol.GetAtoms():
            atoms.append({
                "atomic_num": atom.GetAtomicNum(),
                "formal_charge": atom.GetFormalCharge(),
                "is_aromatic": atom.GetIsAromatic()
            })
        
        bonds = []
        for bond in mol.GetBonds():
            bonds.append({
                "begin_atom_idx": bond.GetBeginAtomIdx(),
                "end_atom_idx": bond.GetEndAtomIdx(),
                "bond_type": bond.GetBondType().name,
                "is_aromatic": bond.GetIsAromatic()
            })
        
        logger.debug(f"Successfully converted SMILES to graph with {len(atoms)} atoms and {len(bonds)} bonds.")
        return MolecularGraph(
            smiles=smiles,
            atoms=atoms,
            bonds=bonds,
            num_atoms=len(atoms),
            num_bonds=len(bonds)
        )
    except Exception as e:
        logger.error(f"Failed to convert SMILES to graph: {e}", exc_info=True)
        return None

@with_exponential_backoff(max_retries=3)
def fetch_nist_record(record_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch a single record from NIST Chemistry WebBook.
    In a real implementation, this would make an HTTP request.
    For this task, we assume the record structure includes 'degradation_pathway'.
    """
    # Placeholder for actual HTTP logic which would use requests
    # This function is decorated with backoff for rate limiting resilience
    logger.info(f"Fetching NIST record: {record_id}")
    # Simulating a successful fetch structure for the logic flow
    # In real execution, this would return data from the API
    return {
        "id": record_id,
        "smiles": "CC(=O)OC", # Example valid SMILES
        "degradation_pathway": "Hydrolysis", # Explicit label required
        "temperature": 298.15,
        "ph": 7.0,
        "uv_intensity": 0.0
    }

def validate_degradation_pathway_label(record: Dict[str, Any]) -> bool:
    """
    Validate the presence of an explicit 'degradation_pathway' label.
    
    Requirement FR-008: Exclude records if this label is missing.
    
    Args:
        record: A dictionary containing polymer record data.
    
    Returns:
        True if 'degradation_pathway' exists and is a non-empty string.
        False otherwise.
    """
    if not isinstance(record, dict):
        logger.warning("Record is not a dictionary; cannot validate label.")
        return False
    
    pathway = record.get("degradation_pathway")
    
    if pathway is None:
        logger.warning(f"Record missing 'degradation_pathway' label. Excluding. Record ID: {record.get('id', 'unknown')}")
        return False
    
    if not isinstance(pathway, str):
        logger.warning(f"Record 'degradation_pathway' is not a string (type: {type(pathway)}). Excluding. Record ID: {record.get('id', 'unknown')}")
        return False
    
    if not pathway.strip():
        logger.warning(f"Record 'degradation_pathway' is empty. Excluding. Record ID: {record.get('id', 'unknown')}")
        return False
    
    logger.debug(f"Record {record.get('id', 'unknown')} has valid pathway label: {pathway}")
    return True

def filter_records_by_pathway_label(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filter a list of records, retaining only those with valid 'degradation_pathway' labels.
    
    This implements the exclusion logic required by FR-008.
    
    Args:
        records: List of raw record dictionaries.
    
    Returns:
        List of records that passed the validation check.
    """
    if not records:
        logger.warning("No records provided to filter.")
        return []
    
    valid_records = []
    excluded_count = 0
    
    logger.info(f"Starting pathway label validation for {len(records)} records.")
    
    for i, record in enumerate(records):
        if validate_degradation_pathway_label(record):
            valid_records.append(record)
        else:
            excluded_count += 1
            record_id = record.get("id", f"index_{i}")
            logger.info(f"Excluded record {record_id} due to missing/invalid degradation pathway label.")
    
    logger.info(f"Pathway label validation complete: {len(valid_records)} kept, {excluded_count} excluded.")
    return valid_records
