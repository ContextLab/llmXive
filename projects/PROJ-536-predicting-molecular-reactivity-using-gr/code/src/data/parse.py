import os
import sys
import logging
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np

try:
    import rdkit
    from rdkit import Chem
    from rdkit.Chem import Descriptors
except ImportError:
    rdkit = None
    Chem = None
    Descriptors = None
    raise ImportError("RDKit is required for this module. Install with: pip install rdkit")

# Import project logging utilities
from src.utils.logging import get_logger, log_invalid_smiles, log_skipped_reaction, log_message

# Constants
DATA_VALIDITY_TARGET = 0.95  # SC-005 Target: >95% valid reactions

def get_atom_features(mol: Chem.Mol) -> List[Dict[str, Any]]:
    """
    Extract atom features from an RDKit molecule.
    Returns a list of dictionaries, one per atom.
    """
    if mol is None:
        return []
    
    features = []
    for atom in mol.GetAtoms():
        feat = {
            "atomic_num": atom.GetAtomicNum(),
            "formal_charge": atom.GetFormalCharge(),
            "num_explicit_hs": atom.GetNumExplicitHs(),
            "num Implicit_hs": atom.GetNumImplicitHs(),
            "hybridization": str(atom.GetHybridization()),
            "is_aromatic": atom.GetIsAromatic(),
        }
        features.append(feat)
    return features

def get_bond_features(mol: Chem.Mol) -> List[Dict[str, Any]]:
    """
    Extract bond features from an RDKit molecule.
    Returns a list of dictionaries, one per bond.
    """
    if mol is None:
        return []
    
    features = []
    for bond in mol.GetBonds():
        feat = {
            "bond_type": str(bond.GetBondType()),
            "is_conjugated": bond.GetIsConjugated(),
            "start_atom_idx": bond.GetBeginAtomIdx(),
            "end_atom_idx": bond.GetEndAtomIdx(),
        }
        features.append(feat)
    return features

def smiles_to_graph(smiles: str) -> Optional[Dict[str, Any]]:
    """
    Convert a SMILES string to a graph representation (atoms, bonds).
    Returns None if the SMILES is invalid.
    """
    if Chem is None:
        raise ImportError("RDKit not available")
    
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    
    # Add hydrogens to ensure implicit Hs are correctly calculated if needed
    mol = Chem.AddHs(mol)
    
    graph_data = {
        "atoms": get_atom_features(mol),
        "bonds": get_bond_features(mol),
        "num_atoms": mol.GetNumAtoms(),
        "num_bonds": mol.GetNumBonds(),
    }
    return graph_data

def parse_reaction_dataframe(df: pd.DataFrame, 
                             reactant_col: str = "reactants_smiles",
                             product_col: str = "product_smiles") -> Tuple[pd.DataFrame, int, int]:
    """
    Parse SMILES columns in a DataFrame into graph representations.
    
    Args:
        df: Input DataFrame containing SMILES columns.
        reactant_col: Name of the reactants SMILES column.
        product_col: Name of the product SMILES column.
        
    Returns:
        Tuple of (processed_df, total_entries, valid_entries)
        processed_df contains new columns: 'reactant_graph', 'product_graph', 'is_valid'
    """
    if Chem is None:
        raise ImportError("RDKit not available")
    
    logger = get_logger(__name__)
    total = len(df)
    valid_count = 0
    
    # Prepare new columns
    reactant_graphs = []
    product_graphs = []
    valid_flags = []
    
    for idx, row in df.iterrows():
        r_smiles = row.get(reactant_col)
        p_smiles = row.get(product_col)
        
        is_valid = True
        r_graph = None
        p_graph = None
        
        # Parse reactants (may be a mixture separated by '.')
        if pd.notna(r_smiles) and isinstance(r_smiles, str):
            # RDKit handles dot-separated mixtures in MolFromSmiles
            r_graph = smiles_to_graph(r_smiles)
            if r_graph is None:
                is_valid = False
                log_invalid_smiles(logger, r_smiles, "reactant", idx)
        
        # Parse product
        if pd.notna(p_smiles) and isinstance(p_smiles, str):
            p_graph = smiles_to_graph(p_smiles)
            if p_graph is None:
                is_valid = False
                log_invalid_smiles(logger, p_smiles, "product", idx)
        
        if not is_valid:
            log_skipped_reaction(logger, idx, f"Invalid SMILES in row {idx}")
            valid_flags.append(False)
            reactant_graphs.append(None)
            product_graphs.append(None)
        else:
            valid_flags.append(True)
            reactant_graphs.append(r_graph)
            product_graphs.append(p_graph)
            valid_count += 1
    
    processed_df = df.copy()
    processed_df['reactant_graph'] = reactant_graphs
    processed_df['product_graph'] = product_graphs
    processed_df['is_valid'] = valid_flags
    
    return processed_df, total, valid_count

def calculate_data_validity(total_entries: int, valid_entries: int) -> float:
    """
    Calculate the percentage of successfully parsed reactions.
    
    Args:
        total_entries: Total number of reaction entries processed.
        valid_entries: Number of entries successfully parsed.
        
    Returns:
        Validity percentage as a float (0.0 to 1.0).
        
    Raises:
        AssertionError: If validity is below the SC-005 target (>95%).
    """
    if total_entries == 0:
        validity = 0.0
    else:
        validity = valid_entries / total_entries
    
    logger = get_logger(__name__)
    log_message(logger, f"Data Validity: {validity:.2%} ({valid_entries}/{total_entries})")
    
    # Assert against SC-005 target
    if validity < DATA_VALIDITY_TARGET:
        error_msg = (
            f"Data validity {validity:.2%} is below the SC-005 target of {DATA_VALIDITY_TARGET:.2%}. "
            f"Please check data quality or parsing logic."
        )
        log_message(logger, error_msg, level=logging.ERROR)
        raise AssertionError(error_msg)
    
    return validity

def main():
    """
    Main entry point for testing the parsing module.
    This function expects a CSV file path as an argument or uses a default test path.
    """
    logger = get_logger(__name__)
    log_message(logger, "Starting data parsing and validity calculation...")
    
    # Example: Load a sample dataset if available, otherwise create a minimal test case
    # In a real pipeline, this would be called after download.py
    try:
        # Check if we have a downloaded file (path might vary based on T012 implementation)
        possible_paths = [
            "data/uspto_subset.csv",
            "data/raw/uspto_subset.csv",
            "data/uspto_sample.csv"
        ]
        input_file = None
        for p in possible_paths:
            if os.path.exists(p):
                input_file = p
                break
        
        if input_file:
            log_message(logger, f"Loading data from {input_file}")
            df = pd.read_csv(input_file)
        else:
            # Fallback: Create a minimal synthetic dataset for testing if no real data is found
            # NOTE: In production, this should ideally fail or require a real download.
            # However, to satisfy the "runnable" constraint for the task without external blocking:
            # We create a small valid set and one invalid set to test the logic.
            # The task requires REAL data if available. If not, we demonstrate the logic.
            log_message(logger, "No real data file found. Creating minimal test data for logic verification.")
            data = {
                "reactants_smiles": ["CCO", "C1=CC=CC=C1", "INVALID_SMILES", "CC(=O)O"],
                "product_smiles": ["CCO", "C1=CC=CC=C1", "C1=CC=CC=C1", "CC(=O)O"],
                "yield": [0.8, 0.9, 0.5, 0.7]
            }
            df = pd.DataFrame(data)
        
        log_message(logger, f"Loaded {len(df)} rows.")
        
        # Parse
        processed_df, total, valid = parse_reaction_dataframe(df)
        
        # Calculate validity
        validity = calculate_data_validity(total, valid)
        
        log_message(logger, f"Data validity check passed: {validity:.2%}")
        
        # Save processed data if real data was used
        if input_file:
            output_path = "data/processed/uspto_parsed.csv"
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            # Drop graph columns for CSV (they are objects)
            csv_df = processed_df.drop(columns=['reactant_graph', 'product_graph'])
            csv_df.to_csv(output_path, index=False)
            log_message(logger, f"Saved processed data to {output_path}")
            
    except Exception as e:
        log_message(logger, f"Error during parsing: {str(e)}", level=logging.ERROR)
        raise

if __name__ == "__main__":
    main()