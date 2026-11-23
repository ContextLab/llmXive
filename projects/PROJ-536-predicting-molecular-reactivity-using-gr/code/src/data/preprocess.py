import os
import sys
import logging
from typing import List, Dict, Any, Optional, Tuple, Set
import pandas as pd
import numpy as np

# RDKit is a core dependency for this project as per requirements.txt
try:
    from rdkit import Chem
    from rdkit.Chem import Descriptors, Crippen, rdMolDescriptors
    from rdkit.Chem.Scaffolds import MurckoScaffold
except ImportError:
    raise ImportError(
        "RDKit is required for scaffold splitting and descriptor calculation. "
        "Install with: pip install rdkit"
    )

from src.utils.logging import get_logger, log_message

# Initialize logger
logger = get_logger(__name__)

def get_murcko_scaffold(smiles: str) -> Optional[str]:
    """
    Extracts the Murcko scaffold SMILES string from a given SMILES string.

    Args:
        smiles: Input SMILES string.

    Returns:
        Canonical SMILES of the Murcko scaffold, or None if parsing fails.
    """
    if not smiles or not isinstance(smiles, str):
        return None

    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None

        scaffold = MurckoScaffold.GetScaffoldForMol(mol)
        # Convert back to SMILES, removing stereochemistry info to ensure
        # consistent grouping if stereochem varies but scaffold is same
        scaffold_smiles = Chem.MolToSmiles(scaffold, isomericSmiles=False)
        return scaffold_smiles
    except Exception as e:
        log_message(logger, "ERROR", f"Failed to generate scaffold for SMILES '{smiles}': {e}")
        return None

# NOTE: The original training script expects a function named ``get_burcko_scaffold``.
# This was a typographical inconsistency.  To maintain backward‑compatibility we
# provide a thin wrapper that forwards to the correctly named implementation.
def get_burcko_scaffold(smiles: str) -> Optional[str]:
    """
    Compatibility wrapper for scaffold extraction.

    The training pipeline historically imported ``get_burcko_scaffold`` from this
    module.  Internally we delegate to :func:`get_murcko_scaffold`, which contains
    the actual implementation.

    Args:
        smiles: Input SMILES string.

    Returns:
        The Murcko scaffold SMILES, or ``None`` if the input cannot be parsed.
    """
    return get_murcko_scaffold(smiles)

def calculate_descriptors(df: pd.DataFrame, smiles_col: str = 'product_smiles') -> pd.DataFrame:
    """
    Calculates molecular descriptors (Molecular Weight, logP, TPSA) for a column of SMILES strings.

    The function adds three new columns to the DataFrame:
        - MW   : Molecular weight (Daltons)
        - logP : Octanol‑water partition coefficient
        - TPSA : Topological Polar Surface Area (Å²)

    Invalid SMILES are logged and result in NaN values for the three descriptors.

    Args:
        df: Input DataFrame containing at least the column specified by ``smiles_col``.
        smiles_col: Name of the column that holds SMILES strings.

    Returns:
        A new DataFrame with the original columns plus the three descriptor columns.
    """
    if smiles_col not in df.columns:
        raise ValueError(f"Column '{smiles_col}' not found in DataFrame. Available columns: {df.columns.tolist()}")

    def _compute_descriptors(smiles: str) -> Tuple[float, float, float]:
        """Return (MW, logP, TPSA) for a single SMILES string."""
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            log_message(logger, "WARNING", f"Invalid SMILES for descriptor calculation: '{smiles}'")
            return (np.nan, np.nan, np.nan)

        mw = Descriptors.MolWt(mol)
        logp = Crippen.MolLogP(mol)
        tpsa = rdMolDescriptors.CalcTPSA(mol)
        return (mw, logp, tpsa)

    # Apply descriptor calculation row‑wise
    descriptor_vals = df[smiles_col].apply(_compute_descriptors)
    descriptor_df = pd.DataFrame(
        descriptor_vals.tolist(),
        columns=['MW', 'logP', 'TPSA'],
        index=df.index
    )

    # Concatenate with the original DataFrame
    result_df = pd.concat([df.reset_index(drop=True), descriptor_df], axis=1)
    return result_df

def add_descriptors_to_dataframe(df: pd.DataFrame, descriptors: Dict[str, Any]) -> pd.DataFrame:
    """
    Merges a dictionary of descriptor Series/DataFrames into the reaction DataFrame.

    This helper is kept for backward compatibility with code that may construct
    descriptor data separately before merging.

    Args:
        df: Original reaction DataFrame.
        descriptors: Mapping where keys are column names and values are array‑like
                    structures (e.g., pandas Series) of the same length as ``df``.

    Returns:
        The DataFrame with the descriptor columns added.
    """
    for col_name, values in descriptors.items():
        if len(values) != len(df):
            raise ValueError(
                f"Length mismatch when adding descriptor '{col_name}': "
                f"{len(values)} values vs {len(df)} rows."
            )
        df[col_name] = values
    return df

def calculate_scaffold_split(
    df: pd.DataFrame,
    smiles_col: str = 'product_smiles',
    split_ratios: Tuple[float, float, float] = (0.8, 0.1, 0.1),
    seed: int = 42,
    min_scaffold_size: int = 1
) -> Dict[str, pd.DataFrame]:
    """
    Performs a Scaffold Split on the dataframe to prevent data leakage.

    Groups reactions by their Murcko Scaffold, then shuffles these groups
    and assigns them to train, validation, and test sets based on split_ratios.

    Args:
        df: Input DataFrame containing reaction data.
        smiles_col: Column name containing the SMILES strings to generate scaffolds from.
        split_ratios: Tuple of (train_ratio, val_ratio, test_ratio). Must sum to 1.0.
        seed: Random seed for reproducibility.
        min_scaffold_size: Minimum number of samples a scaffold group must have to be considered
                           (scaffolds with fewer samples are dropped or handled separately).

    Returns:
        Dictionary with keys 'train', 'val', 'test' containing the split DataFrames.

    Raises:
        ValueError: If split_ratios do not sum to 1.0.
    """
    if not abs(sum(split_ratios) - 1.0) < 1e-6:
        raise ValueError(f"Split ratios must sum to 1.0, got {sum(split_ratios)}")

    if smiles_col not in df.columns:
        raise ValueError(f"Column '{smiles_col}' not found in DataFrame. Available columns: {df.columns.tolist()}")

    logger.info(f"Starting Scaffold Split on column '{smiles_col}' with seed {seed}")

    # 1. Generate Scaffolds
    scaffolds = df[smiles_col].apply(get_murcko_scaffold)

    # Handle None scaffolds (invalid SMILES)
    valid_mask = scaffolds.notna()
    invalid_count = (~valid_mask).sum()
    if invalid_count > 0:
        log_message(logger, "WARNING", f"Found {invalid_count} rows with invalid SMILES, excluding from scaffold split.")

    df_valid = df[valid_mask].copy()
    scaffolds_valid = scaffolds[valid_mask]

    # 2. Group by Scaffold
    scaffold_groups = df_valid.groupby(scaffolds_valid)

    # 3. Get unique scaffolds and shuffle them
    unique_scaffolds = list(scaffold_groups.groups.keys())
    np.random.seed(seed)
    np.random.shuffle(unique_scaffolds)

    # 4. Assign scaffolds to splits
    train_scaffolds = []
    val_scaffolds = []
    test_scaffolds = []

    current_ratio = 0.0

    for scaffold in unique_scaffolds:
        group_size = len(scaffold_groups.get_group(scaffold))
        current_ratio += group_size / len(df_valid)

        if current_ratio <= split_ratios[0]:
            train_scaffolds.append(scaffold)
        elif current_ratio <= split_ratios[0] + split_ratios[1]:
            val_scaffolds.append(scaffold)
        else:
            test_scaffolds.append(scaffold)

    # 5. Construct DataFrames
    def get_split_df(scaffold_list):
        if not scaffold_list:
            return pd.DataFrame(columns=df.columns)
        mask = scaffolds_valid.isin(scaffold_list)
        return df_valid[mask].reset_index(drop=True)

    train_df = get_split_df(train_scaffolds)
    val_df = get_split_df(val_scaffolds)
    test_df = get_split_df(test_scaffolds)

    log_message(logger, "INFO", f"Scaffold Split Complete:")
    log_message(logger, "INFO", f"  Train: {len(train_df)} samples ({len(train_df)/len(df_valid)*100:.1f}%)")
    log_message(logger, "INFO", f"  Val:   {len(val_df)} samples ({len(val_df)/len(df_valid)*100:.1f}%)")
    log_message(logger, "INFO", f"  Test:  {len(test_df)} samples ({len(test_df)/len(df_valid)*100:.1f}%)")
    log_message(logger, "INFO", f"  Unique Scaffolds - Train: {len(set(train_scaffolds))}, Val: {len(set(val_scaffolds))}, Test: {len(set(test_scaffolds))}")

    # Verify no scaffold leakage
    train_s_set = set(train_scaffolds)
    val_s_set = set(val_scaffolds)
    test_s_set = set(test_scaffolds)

    if train_s_set & val_s_set:
        raise RuntimeError("Leakage detected: Scaffolds found in both Train and Val sets.")
    if train_s_set & test_s_set:
        raise RuntimeError("Leakage detected: Scaffolds found in both Train and Test sets.")
    if val_s_set & test_s_set:
        raise RuntimeError("Leakage detected: Scaffolds found in both Val and Test sets.")

    return {
        'train': train_df,
        'val': val_df,
        'test': test_df
    }

def main():
    """
    Main entry point for testing the scaffold split logic.
    This function is intended to be run as a script to demonstrate functionality
    or to be called by the training pipeline.
    """
    # Example usage with a dummy dataframe if run standalone
    # In the real pipeline, this is called from train.py or a preprocessing script
    log_message(logger, "INFO", "Preprocess module loaded. Scaffold split logic available.")
    print("Scaffold Split logic implemented in calculate_scaffold_split().")

if __name__ == "__main__":
    main()