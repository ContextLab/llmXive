"""
Preprocessing module for molecular graph feature extraction and 3D descriptor calculation.

This module handles:
- 2D graph feature extraction (atom type, hybridization, charge)
- Molecular weight calculation
- 3D conformer generation
- SASA and geometric descriptor calculation
"""
import os
import sys
import json
import logging
import hashlib
import traceback
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors, Descriptors, rdDistGeom, AllChem
from rdkit import RDLogger
import pyarrow as pa
import pyarrow.parquet as pq

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.config import MAX_MOLECULES, RANDOM_SEED
from code.utils.logging import get_logger, log_excluded_molecules
from code.utils.validators import count_atoms, is_valid_smiles
from code.data_models.molecule import Molecule

# Disable RDKit warnings
RDLogger.DisableLog('rdApp.*')

logger = get_logger(__name__)

# Constants for 2D feature extraction
ATOM_TYPE_MAP = {
    'C': 0, 'N': 1, 'O': 2, 'S': 3, 'P': 4, 'F': 5, 'Cl': 6, 'Br': 7, 'I': 8, 'H': 9
}
HYBRIDIZATION_MAP = {
    Chem.rdchem.HybridizationType.SP: 0,
    Chem.rdchem.HybridizationType.SP2: 1,
    Chem.rdchem.HybridizationType.SP3: 2,
    Chem.rdchem.HybridizationType.SP3D: 3,
    Chem.rdchem.HybridizationType.SP3D2: 4,
    Chem.rdchem.HybridizationType.OTHER: 5
}
BOND_TYPE_MAP = {
    Chem.rdchem.BondType.SINGLE: 0,
    Chem.rdchem.BondType.DOUBLE: 1,
    Chem.rdchem.BondType.TRIPLE: 2,
    Chem.rdchem.BondType.AROMATIC: 3
}

def load_conformer_params(params_path: str) -> Dict[str, Any]:
    """Load conformer generation parameters from JSON file."""
    try:
        with open(params_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Conformer params file not found: {params_path}")
        raise
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in conformer params file: {params_path}")
        raise

def extract_2d_features(mol: Chem.Mol) -> Tuple[np.ndarray, np.ndarray]:
    """
    Extract 2D graph features from an RDKit molecule.
    
    Returns:
        node_features: np.ndarray of shape (num_atoms, 3)
            [atom_type, hybridization, formal_charge]
        edge_features: np.ndarray of shape (num_bonds, 3)
            [bond_type, conjugated, aromatic]
    """
    # Extract node features
    num_atoms = mol.GetNumAtoms()
    node_features = np.zeros((num_atoms, 3), dtype=np.float32)
    
    for i, atom in enumerate(mol.GetAtoms()):
        # Atom type
        atom_symbol = atom.GetSymbol()
        atom_type = ATOM_TYPE_MAP.get(atom_symbol, 9)  # Default to 'other'
        node_features[i, 0] = atom_type
        
        # Hybridization
        hybridization = atom.GetHybridization()
        hyb_val = HYBRIDIZATION_MAP.get(hybridization, 5)
        node_features[i, 1] = hyb_val
        
        # Formal charge
        formal_charge = atom.GetFormalCharge()
        node_features[i, 2] = float(formal_charge)
    
    # Extract edge features
    num_bonds = mol.GetNumBonds()
    edge_features = np.zeros((num_bonds, 3), dtype=np.float32)
    
    for i, bond in enumerate(mol.GetBonds()):
        # Bond type
        bond_type = bond.GetBondType()
        bt_val = BOND_TYPE_MAP.get(bond_type, 0)
        edge_features[i, 0] = bt_val
        
        # Conjugated
        is_conjugated = 1.0 if bond.GetIsConjugated() else 0.0
        edge_features[i, 1] = is_conjugated
        
        # Aromatic
        is_aromatic = 1.0 if bond.GetIsAromatic() else 0.0
        edge_features[i, 2] = is_aromatic
    
    return node_features, edge_features

def calculate_molecular_weight(mol: Chem.Mol) -> float:
    """Calculate molecular weight using RDKit."""
    return Descriptors.MolWt(mol)

def process_molecule_2d(smiles: str) -> Optional[Dict[str, Any]]:
    """
    Process a single molecule to extract 2D features and calculate MW.
    
    Args:
        smiles: SMILES string of the molecule
        
    Returns:
        Dictionary with smiles, node_features, edge_features, molecular_weight
        or None if molecule is invalid or has >100 atoms
    """
    # Validate SMILES
    if not is_valid_smiles(smiles):
        logger.warning(f"Invalid SMILES: {smiles}")
        return None
    
    # Parse molecule
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        logger.warning(f"Failed to parse SMILES: {smiles}")
        return None
    
    # Check atom count
    atom_count = mol.GetNumAtoms()
    if atom_count > 100:
        return None  # Will be logged by caller
    
    # Extract 2D features
    node_features, edge_features = extract_2d_features(mol)
    
    # Calculate molecular weight
    mw = calculate_molecular_weight(mol)
    
    return {
        'smiles': smiles,
        'node_features': node_features.tolist(),
        'edge_features': edge_features.tolist(),
        'molecular_weight': float(mw)
    }

def process_chunk_2d(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """
    Process a chunk of molecules to extract 2D features.
    
    Args:
        df: DataFrame with 'smiles' column
        
    Returns:
        Tuple of (processed DataFrame, list of excluded SMILES)
    """
    processed_rows = []
    excluded_smiles = []
    
    for idx, row in df.iterrows():
        smiles = row['smiles']
        
        # Process molecule
        result = process_molecule_2d(smiles)
        
        if result is None:
            # Check if it's due to atom count
            mol = Chem.MolFromSmiles(smiles)
            if mol is not None and mol.GetNumAtoms() > 100:
                excluded_smiles.append(smiles)
            # Otherwise it's invalid, already logged
        else:
            processed_rows.append(result)
    
    # Create output DataFrame
    if processed_rows:
        output_df = pd.DataFrame(processed_rows)
    else:
        output_df = pd.DataFrame(columns=['smiles', 'node_features', 'edge_features', 'molecular_weight'])
    
    return output_df, excluded_smiles

def write_graphs_to_parquet(df: pd.DataFrame, output_path: str, conformer_params: Dict[str, Any]) -> None:
    """
    Write processed graphs to Parquet file with metadata.
    
    Args:
        df: DataFrame with graph features
        output_path: Path to output Parquet file
        conformer_params: Conformer generation parameters to embed
    """
    # Calculate hash of conformer params
    params_str = json.dumps(conformer_params, sort_keys=True)
    params_hash = hashlib.sha256(params_str.encode()).hexdigest()
    
    # Add metadata
    table = pa.Table.from_pandas(df)
    existing_metadata = table.schema.metadata or {}
    new_metadata = {
        **existing_metadata,
        b'conformer_config_hash': params_hash.encode(),
        b'conformer_config': json.dumps(conformer_params).encode()
    }
    table = table.replace_schema_metadata(new_metadata)
    
    # Write to Parquet
    pq.write_table(table, output_path)
    logger.info(f"Wrote {len(df)} molecules to {output_path}")

def main():
    """
    Main function to process sampled dataset and extract 2D features.
    
    This function:
    1. Loads the sampled dataset from data/processed/sampled_dataset.parquet
    2. Loads conformer parameters from data/processed/conformer_params.json
    3. Filters molecules with >100 atoms
    4. Extracts 2D features and calculates molecular weight
    5. Writes output to data/processed/graphs_with_features.parquet
    """
    logger.info("Starting 2D graph feature extraction (T014)")
    
    # Define paths
    input_path = project_root / "data" / "processed" / "sampled_dataset.parquet"
    params_path = project_root / "data" / "processed" / "conformer_params.json"
    output_path = project_root / "data" / "processed" / "graphs_with_features.parquet"
    
    # Check input files exist
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)
    
    if not params_path.exists():
        logger.error(f"Conformer params file not found: {params_path}")
        sys.exit(1)
    
    # Load conformer parameters
    conformer_params = load_conformer_params(str(params_path))
    logger.info(f"Loaded conformer parameters: {conformer_params}")
    
    # Load input dataset
    logger.info(f"Loading dataset from {input_path}")
    df = pd.read_parquet(input_path)
    logger.info(f"Loaded {len(df)} molecules")
    
    # Process chunk
    logger.info("Processing molecules for 2D features...")
    processed_df, excluded_smiles = process_chunk_2d(df)
    
    # Log excluded molecules
    if excluded_smiles:
        log_excluded_molecules(len(excluded_smiles), excluded_smiles)
        logger.info(f"Excluded {len(excluded_smiles)} molecules with >100 atoms")
    
    # Log statistics
    logger.info(f"Processed {len(processed_df)} molecules successfully")
    logger.info(f"Excluded {len(excluded_smiles)} molecules (>100 atoms)")
    
    # Write output
    if len(processed_df) > 0:
        write_graphs_to_parquet(processed_df, str(output_path), conformer_params)
        logger.info("2D feature extraction completed successfully")
    else:
        logger.error("No valid molecules processed. Output file not created.")
        sys.exit(1)

if __name__ == "__main__":
    main()