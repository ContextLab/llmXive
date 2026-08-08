import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Iterator

import numpy as np
import pandas as pd
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors, Descriptors
from rdkit.Chem.rdchem import Mol

# Project imports
from code.utils.logging import get_logger, log_excluded_molecules
from code.utils.validators import count_atoms, get_atom_types, get_hybridization, get_charge
from code.utils.config import get_project_root, get_data_dir

logger = get_logger(__name__)

MAX_ATOMS = 100

def calculate_molecular_weight(mol: Mol) -> float:
    """Calculate molecular weight using RDKit."""
    return Descriptors.MolWt(mol)

def extract_2d_features(mol: Mol) -> Tuple[List[List[float]], List[List[float]]]:
    """
    Extract 2D graph features (atom type, hybridization, charge) for a molecule.
    
    Returns:
        node_features: List of feature vectors for each atom
        edge_features: List of edge feature vectors (simplified to adjacency for now)
    """
    num_atoms = mol.GetNumAtoms()
    node_features = []
    
    for atom in mol.GetAtoms():
        # Get atom type (atomic number)
        atom_type = get_atom_types(atom)
        # Get hybridization (encoded as integer)
        hybridization = get_hybridization(atom)
        # Get charge
        charge = get_charge(atom)
        
        # Combine into feature vector [atomic_num, hybridization, charge]
        feature_vector = [float(atom_type), float(hybridization), float(charge)]
        node_features.append(feature_vector)
    
    # Create edge features (adjacency matrix flattened or list of edges)
    # For simplicity, we'll create a list of edge indices and a simple edge feature
    # representing bond type if needed, but for now just adjacency
    edge_features = []
    bonds = mol.GetBonds()
    for bond in bonds:
        i = bond.GetBeginAtomIdx()
        j = bond.GetEndAtomIdx()
        bond_type = int(bond.GetBondType())
        edge_features.append([float(i), float(j), float(bond_type)])
    
    return node_features, edge_features

def process_molecule_2d(smiles: str) -> Optional[Dict[str, Any]]:
    """
    Process a single SMILES string to extract 2D graph features and molecular weight.
    
    Args:
        smiles: SMILES string of the molecule
        
    Returns:
        Dictionary with SMILES, node_features, edge_features, molecular_weight
        or None if processing fails
    """
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            logger.warning(f"Failed to parse SMILES: {smiles}")
            return None
        
        # Check atom count
        atom_count = count_atoms(mol)
        if atom_count > MAX_ATOMS:
            return None
        
        # Extract features
        node_features, edge_features = extract_2d_features(mol)
        
        # Calculate molecular weight
        mw = calculate_molecular_weight(mol)
        
        return {
            'smiles': smiles,
            'node_features': node_features,
            'edge_features': edge_features,
            'molecular_weight': mw,
            'atom_count': atom_count
        }
    except Exception as e:
        logger.error(f"Error processing molecule {smiles}: {e}")
        return None

def process_chunk_2d(chunk: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
    """
    Process a chunk of molecules to extract 2D graph features.
    
    Args:
        chunk: DataFrame with SMILES column
        
    Returns:
        Processed DataFrame and count of excluded molecules
    """
    processed_rows = []
    excluded_count = 0
    excluded_smiles = []
    
    for idx, row in chunk.iterrows():
        smiles = row['smiles']
        result = process_molecule_2d(smiles)
        
        if result is None:
            # Check if it's due to atom count
            try:
                mol = Chem.MolFromSmiles(smiles)
                if mol and count_atoms(mol) > MAX_ATOMS:
                    excluded_count += 1
                    excluded_smiles.append(smiles)
            except:
                pass
            continue
        
        processed_rows.append(result)
    
    # Log excluded molecules
    if excluded_count > 0:
        log_excluded_molecules(excluded_count, excluded_smiles[:10])  # Log first 10 for brevity
        logger.info(f"Excluded {excluded_count} molecules with >{MAX_ATOMS} atoms")
    
    if not processed_rows:
        return pd.DataFrame(), excluded_count
    
    # Convert to DataFrame
    df = pd.DataFrame(processed_rows)
    return df, excluded_count

def save_processed_data(df: pd.DataFrame, output_path: Path):
    """Save processed data to Parquet file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False)
    logger.info(f"Saved processed data to {output_path} with {len(df)} molecules")

def main():
    """Main entry point for 2D graph feature extraction."""
    project_root = get_project_root()
    data_dir = get_data_dir()
    
    # Input from T048
    input_path = data_dir / "raw" / "chunk_0.parquet"
    # If chunk_0 doesn't exist, try to find any chunk
    if not input_path.exists():
        raw_dir = data_dir / "raw"
        chunks = list(raw_dir.glob("chunk_*.parquet"))
        if chunks:
            input_path = sorted(chunks)[0]
        else:
            logger.error("No input parquet files found in data/raw/")
            sys.exit(1)
    
    logger.info(f"Loading data from {input_path}")
    df = pd.read_parquet(input_path)
    
    if 'smiles' not in df.columns:
        logger.error("Input data must contain 'smiles' column")
        sys.exit(1)
    
    logger.info(f"Loaded {len(df)} molecules")
    
    # Process in chunks if needed
    chunk_size = 1000
    all_processed = []
    total_excluded = 0
    
    for i in range(0, len(df), chunk_size):
        chunk = df.iloc[i:i+chunk_size]
        processed_chunk, excluded = process_chunk_2d(chunk)
        total_excluded += excluded
        if not processed_chunk.empty:
            all_processed.append(processed_chunk)
        logger.info(f"Processed chunk {i//chunk_size + 1}, excluded {excluded} molecules")
    
    if not all_processed:
        logger.error("No valid molecules processed")
        sys.exit(1)
    
    final_df = pd.concat(all_processed, ignore_index=True)
    
    # Output path
    output_path = data_dir / "processed" / "graphs_with_features.parquet"
    save_processed_data(final_df, output_path)
    
    # Log final statistics
    logger.info(f"Final dataset: {len(final_df)} molecules, {total_excluded} excluded")
    
    return final_df

if __name__ == "__main__":
    main()
