from __future__ import annotations

import logging
import os
import re
from typing import List, Optional, Dict, Any

from rdkit import Chem

from data_models import PolymerRecord, MolecularGraph
from utils import get_logger

logger = get_logger(__name__)

def validate_smiles(smiles: str) -> bool:
    """Validate if a SMILES string is chemically valid using RDKit."""
    if not smiles or not isinstance(smiles, str):
        logger.warning(f"Invalid SMILES input in preprocess: {smiles}")
        return False
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            logger.warning(f"RDKit failed to parse SMILES in preprocess: {smiles}")
            return False
        return True
    except Exception as e:
        logger.error(f"Exception during SMILES validation in preprocess: {e}")
        return False

def smiles_to_molecular_graph(smiles: str) -> Optional[MolecularGraph]:
    """Convert a valid SMILES string to a MolecularGraph data object."""
    if not validate_smiles(smiles):
        logger.debug(f"Skipping graph conversion for invalid SMILES in preprocess: {smiles}")
        return None
    try:
        mol = Chem.MolFromSmiles(smiles)
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
        
        logger.debug(f"Preprocess: Converted SMILES to graph ({len(atoms)} atoms, {len(bonds)} bonds).")
        return MolecularGraph(
            smiles=smiles,
            atoms=atoms,
            bonds=bonds,
            num_atoms=len(atoms),
            num_bonds=len(bonds)
        )
    except Exception as e:
        logger.error(f"Preprocess: Failed to convert SMILES to graph: {e}", exc_info=True)
        return None

def filter_missing_environmental_data(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filter out records that are missing critical environmental parameters (temp, pH, UV).
    
    Plan Constraint: Records with missing temp/pH/UV MUST be EXCLUDED.
    
    Args:
        records: List of raw record dictionaries.
    
    Returns:
        List of records containing all required environmental data.
    """
    if not records:
        logger.warning("No records provided to filter for environmental data.")
        return []
    
    valid_records = []
    excluded_count = 0
    missing_keys = {"temperature", "ph", "uv_intensity"}
    
    logger.info(f"Filtering {len(records)} records for missing environmental data.")
    
    for i, record in enumerate(records):
        record_id = record.get("id", f"index_{i}")
        missing = []
        
        for key in missing_keys:
            val = record.get(key)
            if val is None or (isinstance(val, float) and val != val): # Check for NaN
                missing.append(key)
        
        if missing:
            excluded_count += 1
            logger.warning(f"Excluded record {record_id}: Missing environmental data - {missing}")
        else:
            valid_records.append(record)
    
    logger.info(f"Environmental data filter complete: {len(valid_records)} kept, {excluded_count} excluded.")
    return valid_records

def filter_polyesters(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filter dataset to retain only polyesters based on functional group detection.
    
    Polyesters typically contain the ester linkage: -C(=O)O-.
    In SMILES, this often appears as patterns like 'C(=O)O' or 'C(=O)OC'.
    
    Args:
        records: List of raw record dictionaries.
    
    Returns:
        List of records identified as polyesters.
    """
    if not records:
        logger.warning("No records provided to filter for polyesters.")
        return []
    
    valid_records = []
    excluded_count = 0
    
    # Regex pattern for ester group: C(=O)O or C(=O)OC
    # This is a simplified heuristic for polyester detection
    ester_pattern = re.compile(r'C\(=O\)O')
    
    logger.info(f"Filtering {len(records)} records for polyester functional groups.")
    
    for i, record in enumerate(records):
        record_id = record.get("id", f"index_{i}")
        smiles = record.get("smiles", "")
        
        if not smiles:
            excluded_count += 1
            logger.warning(f"Excluded record {record_id}: No SMILES string found.")
            continue
        
        if not validate_smiles(smiles):
            excluded_count += 1
            logger.warning(f"Excluded record {record_id}: Invalid SMILES string.")
            continue
        
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            excluded_count += 1
            logger.warning(f"Excluded record {record_id}: RDKit failed to parse SMILES.")
            continue
        
        # Check for ester group using RDKit substructure match or regex on canonical SMILES
        # Using regex on the provided SMILES as a first pass
        if ester_pattern.search(smiles):
            valid_records.append(record)
            logger.debug(f"Record {record_id} identified as polyester.")
        else:
            excluded_count += 1
            logger.debug(f"Excluded record {record_id}: No ester group detected in SMILES.")
    
    logger.info(f"Polyester filter complete: {len(valid_records)} kept, {excluded_count} excluded.")
    return valid_records

def preprocess_polymer_dataset(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Main preprocessing pipeline:
    1. Filter missing environmental data.
    2. Filter for polyesters.
    3. Convert valid SMILES to MolecularGraph objects.
    
    Args:
        records: List of raw record dictionaries.
    
    Returns:
        List of processed PolymerRecord-like dictionaries with graph data.
    """
    logger.info("Starting full preprocessing pipeline.")
    
    # Step 1: Filter environmental data
    step1_records = filter_missing_environmental_data(records)
    if not step1_records:
        logger.error("Dataset empty after environmental data filtering. Aborting.")
        return []
    
    # Step 2: Filter polyesters
    step2_records = filter_polyesters(step1_records)
    if not step2_records:
        logger.error("Dataset empty after polyester filtering. Aborting.")
        return []
    
    # Step 3: Convert to graphs
    processed_records = []
    graph_failures = 0
    
    for record in step2_records:
        smiles = record.get("smiles")
        graph = smiles_to_molecular_graph(smiles)
        
        if graph:
            # Attach graph to record
            processed_record = record.copy()
            processed_record["graph"] = graph
            processed_records.append(processed_record)
        else:
            graph_failures += 1
            logger.warning(f"Failed to generate graph for record {record.get('id', 'unknown')}. Skipping.")
    
    logger.info(f"Preprocessing complete. Total processed: {len(processed_records)}, Graph failures: {graph_failures}.")
    return processed_records
