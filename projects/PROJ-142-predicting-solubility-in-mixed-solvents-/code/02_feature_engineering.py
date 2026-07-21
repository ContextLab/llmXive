"""
Feature Engineering Pipeline for Solubility Prediction.

This module computes molecular descriptors (Morgan fingerprints, topological indices)
and calculates composition-weighted solvent descriptors for mixed solvent systems.
"""
import pandas as pd
import numpy as np
from rdkit import Chem
from rdkit.Chem import Descriptors, AllChem, rdMolDescriptors
from typing import List, Dict, Tuple, Optional
import json
from pathlib import Path

# Import project constants and errors
from utils.constants import DATA_DIR, ARTIFACTS_DIR, PROCESSED_DIR
from utils.errors import CustomDataError, InvalidStoichiometryError
from utils.logging import monitor_resources

# Constants
DESCRIPTOR_LIST = [
    'MolWt', 'MolLogP', 'TPSA', 'NumHDonors', 'NumHAcceptors',
    'NumRotatableBonds', 'NumAromaticRings', 'FractionCSP3'
]

def compute_molecular_descriptors(smiles: str) -> Dict[str, float]:
    """
    Compute standard RDKit descriptors for a single molecule.

    Args:
        smiles: SMILES string of the molecule.

    Returns:
        Dictionary of descriptor name to value.
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise CustomDataError(f"Invalid SMILES string: {smiles}")

    desc = {}
    for name in DESCRIPTOR_LIST:
        try:
            func = getattr(Descriptors, name)
            desc[name] = float(func(mol))
        except Exception:
            desc[name] = np.nan
    
    # Add fingerprint length as a descriptor
    desc['FingerprintLength'] = 2048  # Standard Morgan FP length
    
    return desc

def compute_morgan_fingerprint(smiles: str, radius: int = 2, n_bits: int = 2048) -> np.ndarray:
    """
    Compute Morgan fingerprint for a molecule.

    Args:
        smiles: SMILES string.
        radius: Radius of the fingerprint.
        n_bits: Number of bits in the fingerprint.

    Returns:
        Numpy array of bit values (0 or 1).
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise CustomDataError(f"Invalid SMILES string: {smiles}")
    
    fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius, nBits=n_bits)
    arr = np.zeros((n_bits,), dtype=np.int8)
    AllChem.DataStructs.ConvertToNumpyArray(fp, arr)
    return arr

def calculate_composition_weighted_descriptors(
    df: pd.DataFrame,
    solvent_smiles_col: str = 'solvent_smiles',
    composition_col: str = 'composition_mole_fraction',
    output_path: Optional[Path] = None
) -> pd.DataFrame:
    """
    Calculate composition-weighted solvent descriptors.

    For mixed solvent systems, this computes the weighted average of solvent
    descriptors based on mole fractions. For pure solvents, it simply returns
    the solvent descriptors.

    Args:
        df: Input DataFrame containing solvent SMILES and composition data.
            Expected columns:
            - solvent_smiles: List of SMILES strings for solvents in the mixture
            - composition_mole_fraction: List of mole fractions corresponding to solvents
        solvent_smiles_col: Name of the column containing solvent SMILES.
        composition_col: Name of the column containing mole fractions.
        output_path: Optional path to write the processed DataFrame.

    Returns:
        DataFrame with added composition-weighted descriptor columns.
    """
    # Validate input
    if solvent_smiles_col not in df.columns:
        raise CustomDataError(f"Column '{solvent_smiles_col}' not found in DataFrame")
    if composition_col not in df.columns:
        raise CustomDataError(f"Column '{composition_col}' not found in DataFrame")

    # Initialize new columns for weighted descriptors
    weighted_desc_cols = [f'weighted_{desc}' for desc in DESCRIPTOR_LIST]
    for col in weighted_desc_cols:
        df[col] = np.nan

    # Process each row
    for idx, row in df.iterrows():
        solvents = row[solvent_smiles_col]
        compositions = row[composition_col]

        # Handle case where solvents/compositions might be strings (JSON)
        if isinstance(solvents, str):
            try:
                solvents = json.loads(solvents)
            except json.JSONDecodeError:
                solvents = [solvents]
        
        if isinstance(compositions, str):
            try:
                compositions = json.loads(compositions)
            except json.JSONDecodeError:
                compositions = [1.0]

        # Ensure lists
        if not isinstance(solvents, list):
            solvents = [solvents]
        if not isinstance(compositions, list):
            compositions = [compositions]

        # Normalize compositions if they don't sum to 1.0
        comp_sum = sum(compositions)
        if comp_sum > 0:
            compositions = [c / comp_sum for c in compositions]
        else:
            compositions = [1.0 / len(compositions)] * len(compositions)

        # Calculate weighted descriptors
        weighted_values = {desc: 0.0 for desc in DESCRIPTOR_LIST}
        
        for solvent_smiles, mole_frac in zip(solvents, compositions):
            try:
                desc = compute_molecular_descriptors(solvent_smiles)
                for desc_name in DESCRIPTOR_LIST:
                    if not np.isnan(desc[desc_name]):
                        weighted_values[desc_name] += desc[desc_name] * mole_frac
            except Exception as e:
                # Skip invalid solvents but continue processing
                continue

        # Assign to row
        for desc_name in DESCRIPTOR_LIST:
            col_name = f'weighted_{desc_name}'
            df.at[idx, col_name] = weighted_values[desc_name]

    # Add a column indicating if this is a mixed or pure solvent system
    df['is_mixed_solvent'] = df[solvent_smiles_col].apply(
        lambda x: len(x) > 1 if isinstance(x, list) else False
    )

    if output_path:
        df.to_csv(output_path, index=False)
    
    return df

def add_interaction_terms(df: pd.DataFrame, feature_prefix: str = 'weighted_') -> pd.DataFrame:
    """
    Add explicit interaction terms for mixed solvent systems.

    Creates polynomial and ratio features between weighted descriptors
    to capture non-linear mixing effects.

    Args:
        df: DataFrame with weighted descriptor columns.
        feature_prefix: Prefix for weighted descriptor columns.

    Returns:
        DataFrame with added interaction term columns.
    """
    # Get weighted descriptor columns
    weighted_cols = [col for col in df.columns if col.startswith(feature_prefix)]
    
    if not weighted_cols:
        return df

    # Add interaction terms for mixed solvent systems only
    if 'is_mixed_solvent' in df.columns:
        mask = df['is_mixed_solvent']
    else:
        mask = pd.Series([True] * len(df))

    # Polynomial terms (squares) for key descriptors
    key_descriptors = ['weighted_MolLogP', 'weighted_TPSA', 'weighted_MolWt']
    for col in key_descriptors:
        if col in df.columns:
            new_col = f'{col}_squared'
            df.loc[mask, new_col] = df.loc[mask, col] ** 2

    # Ratio terms
    if 'weighted_MolLogP' in df.columns and 'weighted_TPSA' in df.columns:
        df['logp_tpsa_ratio'] = df['weighted_MolLogP'] / (df['weighted_TPSA'] + 1e-6)

    # Cross terms between top descriptors
    if 'weighted_MolLogP' in df.columns and 'weighted_MolWt' in df.columns:
        df['logp_molwt_interaction'] = df['weighted_MolLogP'] * df['weighted_MolWt']

    return df

def execute_feature_engineering(
    input_path: Path = PROCESSED_DIR / 'cleaned_compositions.csv',
    output_path: Path = PROCESSED_DIR / 'solubility_features.csv'
) -> pd.DataFrame:
    """
    Main execution function for feature engineering pipeline.

    1. Loads cleaned composition data
    2. Computes composition-weighted solvent descriptors
    3. Adds interaction terms
    4. Writes final feature dataset

    Args:
        input_path: Path to input cleaned compositions CSV.
        output_path: Path to output features CSV.

    Returns:
        Final processed DataFrame.
    """
    # Monitor resources
    monitor_resources()

    # Load data
    if not input_path.exists():
        raise CustomDataError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    print(f"Loaded {len(df)} records from {input_path}")

    # Compute weighted descriptors
    print("Computing composition-weighted solvent descriptors...")
    df = calculate_composition_weighted_descriptors(df, output_path=None)

    # Add interaction terms
    print("Adding interaction terms...")
    df = add_interaction_terms(df)

    # Save results
    print(f"Saving features to {output_path}...")
    df.to_csv(output_path, index=False)
    
    print(f"Feature engineering complete. Output: {len(df)} rows, {len(df.columns)} columns")
    return df

if __name__ == "__main__":
    execute_feature_engineering()
