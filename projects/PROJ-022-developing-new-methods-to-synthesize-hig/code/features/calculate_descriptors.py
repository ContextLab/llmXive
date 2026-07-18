"""
Descriptor Calculation Module for Polymer Analysis.

Computes molecular descriptors (VdW volume, H-bond counts, Molecular Weight)
using RDKit from SMILES strings found in the standardized dataset.
"""
import os
import sys
import logging
import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple, Any
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

try:
    from rdkit import Chem
    from rdkit.Chem import Descriptors, rdMolDescriptors
    from rdkit import RDLogger
except ImportError:
    # Fallback for environments without RDKit installed (should not happen in pipeline)
    raise ImportError("RDKit is required for descriptor calculation. Install via: pip install rdkit")

from utils.logging_config import get_logger

# Disable RDKit warnings to keep logs clean
RDLogger.DisableLog('rdApp.*')

logger = get_logger(__name__)

# Constants
DESCRIPTORS_TO_CALCULATE = [
    ('MolecularWeight', Descriptors.MolWt, 'g/mol'),
    ('VdWVolume', rdMolDescriptors.CalcVdWVolume, 'Angstrom^3'),
    ('HBA', rdMolDescriptors.CalcNumHBA, 'count'),
    ('HBD', rdMolDescriptors.CalcNumHBD, 'count'),
    ('NumRotatableBonds', Descriptors.NumRotatableBonds, 'count'),
    ('TPSA', Descriptors.TPSA, 'Angstrom^2'),
]

def calculate_molecular_weight(mol: Chem.Mol) -> float:
    """Calculate molecular weight using RDKit."""
    return Descriptors.MolWt(mol)

def calculate_vdw_volume(mol: Chem.Mol) -> float:
    """Calculate Van der Waals volume using RDKit."""
    return rdMolDescriptors.CalcVdWVolume(mol)

def calculate_hb_counts(mol: Chem.Mol) -> Tuple[int, int]:
    """Calculate H-bond acceptor and donor counts."""
    hba = rdMolDescriptors.CalcNumHBA(mol)
    hbd = rdMolDescriptors.CalcNumHBD(mol)
    return hba, hbd

def calculate_descriptors_for_smiles(smiles: str) -> Optional[Dict[str, Any]]:
    """
    Calculate descriptors for a single SMILES string.
    
    Args:
        smiles: SMILES string representing the molecule.
        
    Returns:
        Dictionary of descriptor values, or None if parsing fails.
    """
    if not isinstance(smiles, str) or not smiles.strip():
        return None

    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            logger.warning(f"Failed to parse SMILES: {smiles}")
            return None

        # Ensure hydrogens are added for accurate volume calculations
        mol = Chem.AddHs(mol)

        descriptors = {}
        
        # Calculate MW and VdW Volume on the molecule with Hs
        descriptors['molecular_weight'] = calculate_molecular_weight(mol)
        descriptors['vdw_volume'] = calculate_vdw_volume(mol)
        
        # Calculate H-bond counts (usually on implicit H structure or explicit, 
        # RDKit handles this internally for these specific functions)
        # Using the original mol (without explicit Hs added) for HBA/HBD is standard
        mol_no_h = Chem.MolFromSmiles(smiles)
        hba, hbd = calculate_hb_counts(mol_no_h)
        descriptors['h_bond_acceptors'] = hba
        descriptors['h_bond_donors'] = hbd
        
        # Additional useful descriptors
        descriptors['num_rotatable_bonds'] = Descriptors.NumRotatableBonds(mol_no_h)
        descriptors['tpsa'] = Descriptors.TPSA(mol_no_h)

        return descriptors

    except Exception as e:
        logger.error(f"Error calculating descriptors for SMILES '{smiles}': {e}")
        return None

def process_dataframe(df: pd.DataFrame, smiles_col: str = 'smiles') -> pd.DataFrame:
    """
    Process a dataframe containing SMILES strings and add descriptor columns.
    
    Args:
        df: Input dataframe with a 'smiles' column.
        smiles_col: Name of the column containing SMILES strings.
        
    Returns:
        Dataframe with new descriptor columns added. Failed calculations result in NaN.
    """
    if smiles_col not in df.columns:
        raise ValueError(f"Column '{smiles_col}' not found in dataframe.")

    logger.info(f"Starting descriptor calculation for {len(df)} rows...")
    
    results = []
    valid_count = 0
    failed_count = 0

    for idx, row in df.iterrows():
        smiles = row[smiles_col]
        desc = calculate_descriptors_for_smiles(smiles)
        
        if desc is not None:
            results.append(desc)
            valid_count += 1
        else:
            # Append None/NaN for failed rows to maintain alignment
            results.append({k: np.nan for k in ['molecular_weight', 'vdw_volume', 'h_bond_acceptors', 'h_bond_donors', 'num_rotatable_bonds', 'tpsa']})
            failed_count += 1

        if (idx + 1) % 100 == 0:
            logger.debug(f"Processed {idx + 1}/{len(df)} molecules...")

    logger.info(f"Descriptor calculation complete. Success: {valid_count}, Failed: {failed_count}")

    # Convert list of dicts to DataFrame
    desc_df = pd.DataFrame(results)
    
    # Concatenate with original dataframe
    # Drop the original smiles column if we want a clean feature matrix, 
    # but typically we keep it or merge back. Here we merge back.
    final_df = pd.concat([df.reset_index(drop=True), desc_df], axis=1)
    
    return final_df

def main():
    """
    Main entry point for the descriptor calculation script.
    Reads from data/processed/standardized_polymers.csv and writes to data/processed/feature_matrix_descriptors.csv.
    """
    # Define paths relative to project root
    input_path = project_root / "data" / "processed" / "standardized_polymers.csv"
    output_path = project_root / "data" / "processed" / "feature_matrix_descriptors.csv"

    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        logger.error("Please run the ingestion pipeline (T016) first to generate standardized_polymers.csv.")
        sys.exit(1)

    try:
        logger.info(f"Loading data from {input_path}")
        df = pd.read_csv(input_path)
        
        # Check for SMILES column
        if 'smiles' not in df.columns:
            # Try common alternatives
            if 'smile' in df.columns:
                df = df.rename(columns={'smile': 'smiles'})
            elif 'SMILES' in df.columns:
                df = df.rename(columns={'SMILES': 'smiles'})
            else:
                raise KeyError("Could not find 'smiles' column in input data.")

        logger.info(f"Processing {len(df)} records...")
        df_processed = process_dataframe(df, smiles_col='smiles')
        
        # Save results
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df_processed.to_csv(output_path, index=False)
        
        logger.info(f"Descriptors saved to {output_path}")
        print(f"Successfully generated {output_path}")
        
    except Exception as e:
        logger.exception(f"Failed to process descriptors: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
