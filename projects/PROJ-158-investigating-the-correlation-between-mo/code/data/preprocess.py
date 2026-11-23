"""
Data preprocessing module for DSSC dataset.
"""
import os
import sys
import logging
from pathlib import Path
from typing import List, Tuple, Optional
import pandas as pd
from rdkit import Chem
from rdkit.Chem import AllChem

from utils.config import get_config, PROCESSED_DATA_DIR
from utils.logger import setup_logger
from utils.data_loader import load_csv, save_csv

logger = setup_logger("preprocess")

def load_raw_data(path: Path) -> pd.DataFrame:
    """Loads the raw CSV file."""
    return load_csv(path)

def remove_salts(smiles: str) -> List[Chem.Mol]:
    """
    Removes salts/counter-ions from a dot-separated SMILES string.
    Returns a list of RDKit Mol objects for the organic fragments.
    """
    try:
        # Split by dot
        parts = smiles.split(".")
        mols = []
        for part in parts:
            mol = Chem.SmilesMol(part)
            if mol:
                # Heuristic: Keep organic molecules (contain Carbon)
                # Or simply keep all non-ionic fragments if logic is complex
                # For this task, we assume all parts are valid molecules and filter later
                # or use a specific salt removal library logic if available.
                # Standard RDKit approach:
                mols.append(mol)
        return mols
    except Exception as e:
        logger.error(f"Error removing salts from {smiles}: {e}")
        return []

def canonicalize_tautomer(smiles: str) -> Optional[Chem.Mol]:
    """
    Canonicalizes tautomers for a given SMILES.
    Returns a RDKit Mol object or None if invalid.
    """
    try:
        mol = Chem.SmilesMol(smiles)
        if not mol:
            return None
        
        # Canonicalize
        Chem.CanonicalizeMol(mol)
        return mol
    except Exception as e:
        logger.error(f"Error canonicalizing {smiles}: {e}")
        return None

def compute_atom_features(mol: Chem.Mol) -> List[int]:
    """Computes atom features (atomic number, hybridization)."""
    # Placeholder implementation
    return [atom.GetAtomicNum() for atom in mol.GetAtoms()]

def compute_bond_features(mol: Chem.Mol) -> List[Tuple[int, int]]:
    """Computes bond features (type, aromaticity)."""
    # Placeholder implementation
    return [(bond.GetBondType(), bond.GetIsAromatic()) for bond in mol.GetBonds()]

def process_molecules(df: pd.DataFrame) -> pd.DataFrame:
    """
    Processes the DataFrame: removes salts, canonicalizes tautomers, handles invalid SMILES.
    """
    processed_rows = []
    
    for idx, row in df.iterrows():
        smiles = row["smiles"]
        try:
            # Remove salts
            mols = remove_salts(smiles)
            if not mols:
                logger.warning(f"No valid molecules found for {smiles}")
                continue
            
            # Select first organic molecule (or aggregate if needed)
            # For simplicity, take the first valid one
            mol = mols[0]
            
            # Canonicalize
            canon_mol = canonicalize_tautomer(Chem.MolToSmiles(mol))
            if not canon_mol:
                continue
            
            canon_smiles = Chem.MolToSmiles(canon_mol)
            
            # Compute features
            atom_features = compute_atom_features(canon_mol)
            bond_features = compute_bond_features(canon_mol)
            
            # Create new row
            new_row = row.copy()
            new_row["canonical_smiles"] = canon_smiles
            new_row["atom_features"] = str(atom_features)
            new_row["bond_features"] = str(bond_features)
            processed_rows.append(new_row)
            
        except Exception as e:
            logger.error(f"Error processing row {idx}: {e}")
            # Log to failed_molecules.log
            with open(PROCESSED_DATA_DIR / "failed_molecules.log", "a") as f:
                f.write(f"SMILES: {smiles} | Error: {str(e)}\n")
    
    return pd.DataFrame(processed_rows)

def save_preprocessed_data(df: pd.DataFrame, output_path: Path) -> None:
    """Saves the preprocessed data."""
    save_csv(df, output_path)

def main():
    """Main entry point for preprocess script."""
    input_path = RAW_DATA_DIR / "dssc_dataset.csv"
    output_csv = PROCESSED_DATA_DIR / "cleaned_data.csv"
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        return

    df = load_raw_data(input_path)
    processed_df = process_molecules(df)
    save_preprocessed_data(processed_df, output_csv)
    logger.info("Preprocessing complete.")

if __name__ == "__main__":
    main()
