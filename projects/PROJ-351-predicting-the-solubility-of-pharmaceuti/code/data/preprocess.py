"""
Preprocessing module for ESOL dataset.

This module handles the conversion of raw SMILES data into graph representations
suitable for GNN training. It processes data in chunks to ensure compatibility
with memory-constrained environments (~7GB RAM limit).

Key features:
- Chunked processing to prevent OOM errors
- RDKit-based molecular feature extraction
- Logging of exclusions and processing statistics
- Output of processed graphs in JSON format
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import pandas as pd
import numpy as np
from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors
import hashlib

# Add parent directory to path for imports if running as script
if __name__ == "__main__":
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.logging_config import setup_logger
from config.seeds import ensure_seeded

# Constants
CHUNK_SIZE = 500  # Process 500 molecules at a time
ATOM_FEATURES_DIM = 64
BOND_FEATURES_DIM = 32

# Atom feature mapping
ATOM_MAP = {
    'C': 0, 'N': 1, 'O': 2, 'F': 3, 'Cl': 4, 'Br': 5, 'I': 6, 'S': 7, 'P': 8,
    'Si': 9, 'B': 10, 'As': 11, 'Se': 12, 'Te': 13, 'Xe': 14, 'He': 15, 'Ne': 16,
    'Ar': 17, 'Kr': 18, 'Rn': 19, 'Hg': 20, 'Pb': 21, 'Sn': 22, 'Bi': 23, 'Zn': 24,
    'Cu': 25, 'Fe': 26, 'Mn': 27, 'Co': 28, 'Ni': 29, 'Ti': 30, 'V': 31, 'Cr': 32,
    'Mg': 33, 'Ca': 34, 'Na': 35, 'K': 36, 'Li': 37, 'Al': 38, 'Ag': 39, 'Au': 40,
    'Pt': 41, 'Pd': 42, 'Rh': 43, 'Ir': 44, 'Ru': 45, 'Os': 46, 'Re': 47, 'Mo': 48,
    'W': 49, 'Ta': 50, 'Nb': 51, 'Zr': 52, 'Hf': 53, 'Sc': 54, 'Y': 55, 'La': 56,
    'Ce': 57, 'Pr': 58, 'Nd': 59, 'Sm': 60, 'Eu': 61, 'Gd': 62, 'Tb': 63
}

# Bond feature mapping
BOND_MAP = {
    'SINGLE': 0, 'DOUBLE': 1, 'TRIPLE': 2, 'AROMATIC': 3
}

logger = None

def setup_logging():
    """Initialize logging for this module."""
    global logger
    logger = setup_logger('preprocess', 'data/logs/preprocess.log')
    return logger

def get_atom_features(mol: Chem.Mol, atom_idx: int) -> List[float]:
    """
    Extract features for a single atom.
    
    Args:
        mol: RDKit molecule object
        atom_idx: Index of the atom in the molecule
        
    Returns:
        List of atom features
    """
    atom = mol.GetAtomWithIdx(atom_idx)
    features = [0.0] * ATOM_FEATURES_DIM
    
    # Element type
    symbol = atom.GetSymbol()
    if symbol in ATOM_MAP:
        features[ATOM_MAP[symbol]] = 1.0
    else:
        # Unknown element - use a fallback index
        features[63] = 1.0
        
    # Degree
    degree = atom.GetDegree()
    if degree < 10:
        features[64 + degree] = 1.0
        
    # Hybridization
    hybridization = atom.GetHybridization()
    hybrid_map = {
        Chem.rdchem.HybridizationType.SP: 0,
        Chem.rdchem.HybridizationType.SP2: 1,
        Chem.rdchem.HybridizationType.SP3: 2,
        Chem.rdchem.HybridizationType.SP3D: 3,
        Chem.rdchem.HybridizationType.SP3D2: 4,
        Chem.rdchem.HybridizationType.OTHER: 5
    }
    if hybridization in hybrid_map:
        features[74 + hybrid_map[hybridization]] = 1.0
        
    # Formal charge
    charge = atom.GetFormalCharge()
    if -5 <= charge <= 5:
        features[80 + charge + 5] = 1.0
        
    # Number of hydrogens
    num_h = atom.GetTotalNumHs()
    if num_h < 10:
        features[90 + num_h] = 1.0
        
    # Aromaticity
    if atom.GetIsAromatic():
        features[100] = 1.0
        
    return features

def get_bond_features(mol: Chem.Mol, bond_idx: int) -> List[float]:
    """
    Extract features for a single bond.
    
    Args:
        mol: RDKit molecule object
        bond_idx: Index of the bond in the molecule
        
    Returns:
        List of bond features
    """
    bond = mol.GetBondWithIdx(bond_idx)
    features = [0.0] * BOND_FEATURES_DIM
    
    # Bond type
    bond_type = bond.GetBondType().name
    if bond_type in BOND_MAP:
        features[BOND_MAP[bond_type]] = 1.0
    else:
        features[4] = 1.0  # Unknown/other
        
    # Conjugation
    if bond.GetIsConjugated():
        features[5] = 1.0
        
    # In ring
    if bond.IsInRing():
        features[6] = 1.0
        
    return features

def process_molecule(smiles: str, logS: float) -> Optional[Dict[str, Any]]:
    """
    Process a single molecule from SMILES string to graph representation.
    
    Args:
        smiles: SMILES string of the molecule
        logS: Experimental logS value
        
    Returns:
        Dictionary containing graph data or None if invalid
    """
    global logger
    
    # Parse SMILES
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        if logger:
            logger.warning(f"Invalid SMILES: {smiles}")
        return None
        
    # Get number of atoms and bonds
    num_atoms = mol.GetNumAtoms()
    num_bonds = mol.GetNumBonds()
    
    if num_atoms == 0:
        if logger:
            logger.warning(f"Molecule with no atoms: {smiles}")
        return None
        
    # Extract atom features
    atom_features = []
    for i in range(num_atoms):
        atom_feat = get_atom_features(mol, i)
        atom_features.append(atom_feat)
        
    # Extract bond features and adjacency
    bond_features = []
    adjacency = np.zeros((num_atoms, num_atoms), dtype=np.int32)
    
    for i in range(num_bonds):
        bond = mol.GetBondWithIdx(i)
        bond_feat = get_bond_features(mol, i)
        bond_features.append(bond_feat)
        
        # Update adjacency matrix
        atom1_idx = bond.GetBeginAtomIdx()
        atom2_idx = bond.GetEndAtomIdx()
        adjacency[atom1_idx, atom2_idx] = bond.GetBondType().num + 1
        adjacency[atom2_idx, atom1_idx] = bond.GetBondType().num + 1
        
    # Create graph dictionary
    graph_data = {
        'smiles': smiles,
        'logS': logS,
        'num_atoms': num_atoms,
        'num_bonds': num_bonds,
        'atom_features': atom_features,
        'bond_features': bond_features,
        'adjacency': adjacency.tolist()
    }
    
    return graph_data

def load_and_preprocess(input_path: str, output_path: str, chunk_size: int = CHUNK_SIZE) -> Dict[str, Any]:
    """
    Load raw CSV and preprocess in chunks to handle large datasets.
    
    This function processes the ESOL dataset in chunks to avoid memory issues
    with large files. It validates each molecule, logs exclusions, and saves
    the processed data incrementally.
    
    Args:
        input_path: Path to raw CSV file
        output_path: Path to save processed data
        chunk_size: Number of molecules to process at once
        
    Returns:
        Dictionary containing processing statistics
    """
    global logger
    if logger is None:
        setup_logging()
        
    logger.info(f"Starting preprocessing: {input_path} -> {output_path}")
    
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Statistics tracking
    stats = {
        'total_rows': 0,
        'valid_molecules': 0,
        'invalid_smiles': 0,
        'excluded_logS': 0,
        'processing_time': 0.0
    }
    
    start_time = time.time()
    
    # Process in chunks
    processed_graphs = []
    chunk_results = []
    
    try:
        # Read CSV in chunks
        chunk_iter = pd.read_csv(input_path, chunksize=chunk_size)
        
        for chunk_idx, chunk in enumerate(chunk_iter):
            logger.info(f"Processing chunk {chunk_idx + 1}")
            
            for _, row in chunk.iterrows():
                stats['total_rows'] += 1
                
                # Validate logS
                logS = row.get('measured logS', row.get('logS', None))
                if pd.isna(logS):
                    stats['excluded_logS'] += 1
                    continue
                    
                # Get SMILES
                smiles = row.get('SMILES', row.get('smiles', None))
                if pd.isna(smiles):
                    stats['invalid_smiles'] += 1
                    continue
                    
                # Process molecule
                graph_data = process_molecule(str(smiles), float(logS))
                if graph_data is not None:
                    processed_graphs.append(graph_data)
                    stats['valid_molecules'] += 1
                else:
                    stats['invalid_smiles'] += 1
                    
            # Save chunk to disk periodically to manage memory
            if len(processed_graphs) >= 1000:
                chunk_file = f"{output_path}.part_{chunk_idx}.json"
                with open(chunk_file, 'w') as f:
                    json.dump(processed_graphs, f)
                chunk_results.append(chunk_file)
                logger.info(f"Saved chunk {chunk_idx + 1} to {chunk_file}")
                processed_graphs = []
                
    except Exception as e:
        logger.error(f"Error during preprocessing: {str(e)}")
        raise
        
    # Save remaining processed data
    if processed_graphs:
        final_chunk_file = f"{output_path}.final.json"
        with open(final_chunk_file, 'w') as f:
            json.dump(processed_graphs, f)
        chunk_results.append(final_chunk_file)
        logger.info(f"Saved final chunk to {final_chunk_file}")
        
    # Merge all chunks into final output
    logger.info("Merging chunks into final output...")
    all_graphs = []
    for chunk_file in chunk_results:
        try:
            with open(chunk_file, 'r') as f:
                all_graphs.extend(json.load(f))
            os.remove(chunk_file)  # Clean up temporary chunk files
        except Exception as e:
            logger.warning(f"Error reading chunk {chunk_file}: {str(e)}")
            
    # Save final merged data
    with open(output_path, 'w') as f:
        json.dump(all_graphs, f)
        
    stats['processing_time'] = time.time() - start_time
    
    logger.info(f"Preprocessing complete. Total: {stats['total_rows']}, "
               f"Valid: {stats['valid_molecules']}, "
               f"Invalid SMILES: {stats['invalid_smiles']}, "
               f"Excluded logS: {stats['excluded_logS']}")
               
    return stats

def main():
    """Main entry point for preprocessing script."""
    import argparse
    import time
    
    parser = argparse.ArgumentParser(description='Preprocess ESOL dataset')
    parser.add_argument('--input', type=str, required=True, 
                      help='Path to raw CSV file')
    parser.add_argument('--output', type=str, required=True,
                      help='Path to save processed data')
    parser.add_argument('--chunk-size', type=int, default=CHUNK_SIZE,
                      help='Number of molecules to process per chunk')
    parser.add_argument('--seed', type=int, default=42,
                      help='Random seed for reproducibility')
                      
    args = parser.parse_args()
    
    # Set seed for reproducibility
    ensure_seeded(args.seed)
    
    # Setup logging
    setup_logging()
    
    logger.info("Starting ESOL dataset preprocessing")
    logger.info(f"Input: {args.input}")
    logger.info(f"Output: {args.output}")
    logger.info(f"Chunk size: {args.chunk_size}")
    
    # Run preprocessing
    try:
        stats = load_and_preprocess(
            args.input, 
            args.output, 
            chunk_size=args.chunk_size
        )
        
        # Save statistics
        stats_path = args.output.replace('.json', '_stats.json')
        with open(stats_path, 'w') as f:
            json.dump(stats, f, indent=2)
            
        logger.info(f"Statistics saved to {stats_path}")
        logger.info("Preprocessing completed successfully")
        
    except Exception as e:
        logger.error(f"Preprocessing failed: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()