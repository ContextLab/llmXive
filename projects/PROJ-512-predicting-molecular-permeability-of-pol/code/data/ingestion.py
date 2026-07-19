"""
Data ingestion module for polymer permeability data.

This module handles fetching data from NIST/PubChem, generating simulation data
as a fallback, parsing SMILES into graphs, and cleaning the dataset.
"""
import os
import sys
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
import hashlib
import json
import pandas as pd
from pathlib import Path

from data.utils import (
    set_seed, get_seed, get_seed_hash, ensure_seed_initialized,
    setup_logging, ValidationResult, validate_smiles, validate_mw,
    validate_record, validate_dataset
)
from data.logging_config import get_logger
from models.polymer_graph import PolymerGraph
from models.permeability_record import PermeabilityRecord

# Import RDKit safely
try:
    from rdkit import Chem
    from rdkit.Chem import Descriptors, rdMolDescriptors
    HAS_RDKIT = True
except ImportError:
    HAS_RDKIT = False

logger = get_logger(__name__)

class DataUnavailableError(Exception):
    """Raised when data cannot be fetched or generated."""
    pass

def calculate_file_checksum(file_path: str) -> str:
    """
    Calculate SHA256 checksum of a file.
    
    Args:
        file_path: Path to the file.
    
    Returns:
        Hexadecimal checksum string.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def save_checksums(checksums: Dict[str, str], output_path: str) -> None:
    """
    Save checksums to a JSON file.
    
    Args:
        checksums: Dictionary mapping file paths to checksums.
        output_path: Path to the output JSON file.
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(checksums, f, indent=2)
    logger.info(f"Saved checksums to {output_path}")

def smiles_to_polymer_graph(smiles: str) -> Optional[PolymerGraph]:
    """
    Convert a SMILES string to a PolymerGraph object.
    
    Args:
        smiles: SMILES string representation of the molecule.
    
    Returns:
        PolymerGraph object or None if conversion fails.
    """
    if not HAS_RDKIT:
        logger.error("RDKit is not installed. Cannot convert SMILES to graph.")
        return None
    
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        logger.warning(f"Failed to parse SMILES: {smiles}")
        return None
    
    # Extract nodes (atoms)
    nodes = []
    for atom in mol.GetAtoms():
        node_data = {
            'atom_type': atom.GetAtomicNum(),
            'hybridization': int(atom.GetHybridization()),
            'formal_charge': atom.GetFormalCharge(),
            'is_aromatic': atom.GetIsAromatic()
        }
        nodes.append(node_data)
    
    # Extract edges (bonds)
    edges = []
    edge_attrs = []
    for bond in mol.GetBonds():
        start = bond.GetBeginAtomIdx()
        end = bond.GetEndAtomIdx()
        bond_type = int(bond.GetBondType())
        edges.append([start, end])
        edge_attrs.append({
            'bond_type': bond_type,
            'is_aromatic': bond.GetIsAromatic()
        })
    
    return PolymerGraph(
        nodes=nodes,
        edges=edges,
        edge_attributes=edge_attrs,
        smiles=smiles
    )

def calculate_mw(smiles: str) -> Optional[float]:
    """
    Calculate molecular weight from SMILES.
    
    Args:
        smiles: SMILES string.
    
    Returns:
        Molecular weight or None if calculation fails.
    """
    if not HAS_RDKIT:
        return None
    
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    
    return Descriptors.MolWt(mol)

def fetch_nist_pubchem_data() -> Tuple[List[Dict[str, Any]], str]:
    """
    Fetch polymer data from NIST/PubChem.
    
    Returns:
        Tuple of (data list, source identifier).
    
    Raises:
        DataUnavailableError: If data cannot be fetched.
    """
    # Placeholder for actual NIST/PubChem fetch logic
    # In a real implementation, this would make HTTP requests or use an API
    logger.warning("Real NIST/PubChem fetch not implemented. Raising DataUnavailableError.")
    raise DataUnavailableError("Real data source unavailable. Falling back to simulation.")

def generate_simulation_data() -> List[Dict[str, Any]]:
    """
    Generate synthetic polymer data using the simulation module.
    
    Returns:
        List of data records.
    """
    from data.simulation import generate_polymer_graphs, save_simulation_data
    
    # Generate simulation data
    graphs, records = generate_polymer_graphs(num_samples=1000)
    
    # Convert to list of dicts for processing
    data = []
    for i, record in enumerate(records):
        data.append({
            'smiles': graphs[i].smiles,
            'permeability': record.log_permeability,
            'mw': calculate_mw(graphs[i].smiles)
        })
    
    return data

def process_dataset(
    data: List[Dict[str, Any]],
    exclude_small_mols: bool = False
) -> Tuple[List[PermeabilityRecord], List[str]]:
    """
    Process a dataset into PermeabilityRecord objects.
    
    Args:
        data: List of raw data records.
        exclude_small_mols: Whether to exclude molecules with MW < 1000.
    
    Returns:
        Tuple of (list of PermeabilityRecord, list of excluded SMILES).
    """
    records = []
    excluded_smiles = []
    
    for item in data:
        smiles = item.get('smiles')
        permeability = item.get('permeability')
        
        # Validate SMILES
        if not smiles:
            logger.warning("Skipping record with missing SMILES.")
            continue
        
        validation = validate_smiles(smiles)
        if not validation.is_valid:
            logger.warning(f"Skipping invalid SMILES: {smiles}. Errors: {validation.errors}")
            continue
        
        # Calculate MW
        mw = calculate_mw(smiles)
        if mw is None:
            logger.warning(f"Could not calculate MW for SMILES: {smiles}")
            continue
        
        # Check MW threshold
        if exclude_small_mols and mw < 1000:
            excluded_smiles.append(smiles)
            logger.info(f"Excluded small molecule (MW={mw}): {smiles}")
            continue
        
        # Create PermeabilityRecord
        try:
            record = PermeabilityRecord(
                smiles=smiles,
                log_permeability=permeability,
                molecular_weight=mw
            )
            records.append(record)
        except Exception as e:
            logger.error(f"Failed to create PermeabilityRecord for {smiles}: {e}")
            continue
    
    return records, excluded_smiles

def clean_data(
    records: List[PermeabilityRecord]
) -> Tuple[List[PermeabilityRecord], Dict[str, Any]]:
    """
    Clean the dataset by removing duplicates and invalid entries.
    
    Args:
        records: List of PermeabilityRecord objects.
    
    Returns:
        Tuple of (cleaned records, statistics dict).
    """
    seen_smiles = {}
    cleaned_records = []
    stats = {
        'total_input': len(records),
        'duplicates_removed': 0,
        'missing_permeability_removed': 0
    }
    
    for record in records:
        smiles = record.smiles
        
        # Check for missing permeability
        if record.log_permeability is None:
            stats['missing_permeability_removed'] += 1
            continue
        
        # Handle duplicates
        if smiles in seen_smiles:
            # Average the permeability values
            seen_smiles[smiles].append(record.log_permeability)
            stats['duplicates_removed'] += 1
        else:
            seen_smiles[smiles] = [record.log_permeability]
    
    # Create averaged records
    for smiles, values in seen_smiles.items():
        avg_permeability = sum(values) / len(values)
        # Find the original record to get MW
        original_record = next((r for r in records if r.smiles == smiles), None)
        if original_record:
            cleaned_records.append(PermeabilityRecord(
                smiles=smiles,
                log_permeability=avg_permeability,
                molecular_weight=original_record.molecular_weight
            ))
    
    stats['total_cleaned'] = len(cleaned_records)
    return cleaned_records, stats

def main():
    """Main entry point for data ingestion."""
    # Setup logging
    setup_logging(level="INFO", log_to_file=True)
    ensure_seed_initialized()
    
    logger.info("Starting data ingestion pipeline.")
    
    # Attempt to fetch real data
    data = []
    source = "unknown"
    try:
        data, source = fetch_nist_pubchem_data()
        logger.info(f"Fetched data from {source}")
    except DataUnavailableError as e:
        logger.warning(f"Real data fetch failed: {e}. Using simulation fallback.")
        data = generate_simulation_data()
        source = "simulation"
    
    # Save raw data
    raw_data_path = "projects/PROJ-512-predicting-molecular-permeability-of-pol/code/data/raw/nist_polymer_raw.csv"
    if source == "simulation":
        raw_data_path = "projects/PROJ-512-predicting-molecular-permeability-of-pol/code/data/raw/simulation_data.csv"
    
    df = pd.DataFrame(data)
    df.to_csv(raw_data_path, index=False)
    logger.info(f"Saved raw data to {raw_data_path}")
    
    # Calculate checksums
    checksum = calculate_file_checksum(raw_data_path)
    checksums = {raw_data_path: checksum}
    save_checksums(
        checksums,
        "projects/PROJ-512-predicting-molecular-permeability-of-pol/code/data/raw/checksums.json"
    )
    
    # Process dataset
    records, excluded = process_dataset(data, exclude_small_mols=False)
    logger.info(f"Processed {len(records)} valid records. Excluded {len(excluded)} small molecules.")
    
    # Clean data
    cleaned_records, stats = clean_data(records)
    logger.info(f"Cleaned dataset: {stats}")
    
    # Save cleaned data to HDF5 (handled by save_dataset module)
    from data.save_dataset import save_to_hdf5
    save_to_hdf5(cleaned_records, "projects/PROJ-512-predicting-molecular-permeability-of-pol/code/data/processed/polymers.h5")
    
    logger.info("Data ingestion pipeline completed successfully.")

if __name__ == "__main__":
    main()
