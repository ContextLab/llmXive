import os
import sys
import logging
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np

try:
    from rdkit import Chem
    from rdkit.Chem import AllChem
except ImportError:
    raise ImportError("RDKit is required. Install it via: pip install rdkit")

from src.utils.logging import get_logger, log_invalid_smiles, log_skipped_reaction

# Constants
DATA_VALIDITY_TARGET = 0.95  # SC-005 target: >95% valid reactions


def get_atom_features(mol: Any) -> List[Dict[str, Any]]:
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
            "degree": atom.GetDegree(),
            "formal_charge": atom.GetFormalCharge(),
            "hybridization": str(atom.GetHybridization()),
            "is_aromatic": atom.GetIsAromatic(),
            "num_hydrogens": atom.GetTotalNumHs(),
        }
        features.append(feat)
    return features


def get_bond_features(mol: Any) -> List[Dict[str, Any]]:
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
            "is_in_ring": bond.IsInRing(),
            "start_atom_idx": bond.GetBeginAtomIdx(),
            "end_atom_idx": bond.GetEndAtomIdx(),
        }
        features.append(feat)
    return features


def smiles_to_graph(smiles: str) -> Optional[Dict[str, Any]]:
    """
    Convert a SMILES string to a graph representation (atoms, bonds).
    Returns None if SMILES is invalid.
    """
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
        
        # Sanitize to catch common issues
        Chem.SanitizeMol(mol)
        
        return {
            "atoms": get_atom_features(mol),
            "bonds": get_bond_features(mol),
            "num_atoms": mol.GetNumAtoms(),
            "num_bonds": mol.GetNumBonds(),
        }
    except Exception:
        return None


def parse_reaction_dataframe(df: pd.DataFrame) -> Tuple[pd.DataFrame, int, int]:
    """
    Parse SMILES columns in a DataFrame into graph representations.
    
    Args:
        df: DataFrame with 'reactants_smiles' and 'product_smiles' columns.
    
    Returns:
        Tuple of (processed_df, valid_count, invalid_count)
        processed_df has new columns 'reactants_graph' and 'product_graph'.
    """
    logger = get_logger(__name__)
    valid_count = 0
    invalid_count = 0
    
    processed_rows = []
    
    for idx, row in df.iterrows():
        reactants_smiles = row.get("reactants_smiles", "")
        product_smiles = row.get("product_smiles", "")
        
        if not isinstance(reactants_smiles, str) or not isinstance(product_smiles, str):
            log_skipped_reaction(logger, idx, "Non-string SMILES")
            invalid_count += 1
            processed_rows.append({**row, "reactants_graph": None, "product_graph": None, "is_valid": False})
            continue
        
        reactants_graph = smiles_to_graph(reactants_smiles)
        product_graph = smiles_to_graph(product_smiles)
        
        if reactants_graph is None or product_graph is None:
            log_invalid_smiles(logger, idx, reactants_smiles, product_smiles)
            invalid_count += 1
            processed_rows.append({**row, "reactants_graph": None, "product_graph": None, "is_valid": False})
        else:
            valid_count += 1
            processed_rows.append({**row, "reactants_graph": reactants_graph, "product_graph": product_graph, "is_valid": True})
    
    processed_df = pd.DataFrame(processed_rows)
    return processed_df, valid_count, invalid_count


def calculate_data_validity(df: pd.DataFrame, target: float = DATA_VALIDITY_TARGET) -> Dict[str, Any]:
    """
    Calculate and report the percentage of successfully parsed reactions.
    
    This function implements the requirement from SC-005:
    "The pipeline must successfully parse >95% of the raw reaction data."
    
    Args:
        df: A DataFrame containing parsed reaction data with an 'is_valid' column.
        target: The minimum validity threshold (default 0.95 for 95%).
    
    Returns:
        A dictionary containing validity statistics.
    
    Raises:
        ValueError: If the validity percentage is below the target threshold.
    """
    if "is_valid" not in df.columns:
        raise ValueError("DataFrame must contain an 'is_valid' column to calculate validity.")
    
    total = len(df)
    if total == 0:
        raise ValueError("Cannot calculate validity on an empty DataFrame.")
    
    valid_count = df["is_valid"].sum()
    validity_percentage = (valid_count / total) * 100
    
    logger = get_logger(__name__)
    
    result = {
        "total_reactions": total,
        "valid_reactions": int(valid_count),
        "invalid_reactions": total - int(valid_count),
        "validity_percentage": validity_percentage,
        "target_percentage": target * 100,
        "meets_target": validity_percentage >= (target * 100)
    }
    
    log_message(
        logger, 
        f"Data Validity Report: {validity_percentage:.2f}% valid ({valid_count}/{total} reactions). "
        f"Target: {target*100:.2f}%. Status: {'PASS' if result['meets_target'] else 'FAIL'}"
    )
    
    if not result["meets_target"]:
        raise ValueError(
            f"Data validity {validity_percentage:.2f}% is below the required target of {target*100:.2f}% "
            f"as per SC-005. Please check data quality or parsing logic."
        )
    
    return result


def main():
    """
    Main entry point for the parse module.
    Demonstrates the data validity calculation workflow.
    """
    logger = get_logger(__name__)
    logger.info("Starting SMILES to Graph parsing and validity calculation.")
    
    # Example usage (in a real scenario, this would load from a file)
    # This block is primarily for documentation of the API usage
    sample_data = {
        "reactants_smiles": ["CCO", "invalid_smiles", "c1ccccc1"],
        "product_smiles": ["CCO", "CC(=O)O", "c1ccccc1C(=O)O"],
        "yield": [0.8, 0.5, 0.9]
    }
    df = pd.DataFrame(sample_data)
    
    parsed_df, valid, invalid = parse_reaction_dataframe(df)
    logger.info(f"Parsed {valid} valid, {invalid} invalid.")
    
    validity_stats = calculate_data_validity(parsed_df)
    logger.info(f"Validity Stats: {validity_stats}")
    
    return validity_stats


if __name__ == "__main__":
    main()