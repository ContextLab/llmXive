"""
Scaffold-based train/test split utility.

Implements a structural diversity split to prevent data leakage by ensuring
that molecules with the same Bemis-Murcko scaffold are not split across
training and testing sets.
"""

import logging
from typing import Tuple, List, Optional
import pandas as pd
import numpy as np
from rdkit import Chem
from rdkit.Chem.Scaffolds import MurckoScaffold

from config import SEED

logger = logging.getLogger(__name__)


def get_murcko_scaffold(smiles: str) -> Optional[str]:
    """
    Extract the Bemis-Murcko scaffold from a SMILES string.

    Args:
        smiles: SMILES string of the molecule.

    Returns:
        Canonical SMILES of the scaffold, or None if extraction fails.
    """
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
        scaffold = MurckoScaffold.GetScaffoldForMol(mol)
        # Remove stereochemistry and return canonical SMILES
        Chem.RemoveStereochemistry(scaffold)
        return Chem.MolToSmiles(scaffold)
    except Exception as e:
        logger.debug(f"Failed to extract scaffold from {smiles}: {e}")
        return None


def scaffold_split(
    df: pd.DataFrame,
    smiles_col: str = "smiles",
    train_ratio: float = 0.8,
    seed: int = SEED
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Perform a scaffold-based train/test split.

    Groups molecules by their Bemis-Murcko scaffold, then splits the
    scaffold groups rather than individual molecules to ensure structural
    diversity between train and test sets.

    Args:
        df: DataFrame containing SMILES strings and target values.
        smiles_col: Column name containing SMILES strings.
        train_ratio: Fraction of scaffolds to use for training (default 0.8).
        seed: Random seed for reproducibility.

    Returns:
        Tuple of (train_df, test_df) DataFrames.

    Raises:
        ValueError: If the DataFrame is empty or contains no valid molecules.
    """
    if df.empty:
        raise ValueError("Input DataFrame is empty.")

    if smiles_col not in df.columns:
        raise ValueError(f"Column '{smiles_col}' not found in DataFrame.")

    # Compute scaffolds for all molecules
    logger.info("Computing Bemis-Murcko scaffolds...")
    df_with_scaffold = df.copy()
    df_with_scaffold["scaffold"] = df_with_scaffold[smiles_col].apply(get_murcko_scaffold)

    # Filter out molecules where scaffold extraction failed
    valid_mask = df_with_scaffold["scaffold"].notna()
    if not valid_mask.all():
        invalid_count = (~valid_mask).sum()
        logger.warning(f"Skipping {invalid_count} molecules with invalid scaffolds.")
        df_with_scaffold = df_with_scaffold[valid_mask]

    if df_with_scaffold.empty:
        raise ValueError("No valid molecules with extractable scaffolds found.")

    # Group by scaffold and count molecules per scaffold
    scaffold_counts = df_with_scaffold.groupby("scaffold").size().reset_index(name="count")

    # Shuffle scaffolds deterministically
    np.random.seed(seed)
    shuffled_scaffolds = scaffold_counts["scaffold"].sample(frac=1, random_state=seed).reset_index(drop=True)

    # Determine split point
    n_scaffolds = len(shuffled_scaffolds)
    train_n_scaffolds = int(np.ceil(train_ratio * n_scaffolds))
    train_scaffolds = set(shuffled_scaffolds.iloc[:train_n_scaffolds])

    # Split the dataframe based on scaffold membership
    train_mask = df_with_scaffold["scaffold"].isin(train_scaffolds)
    train_df = df_with_scaffold[train_mask].drop(columns=["scaffold"])
    test_df = df_with_scaffold[~train_mask].drop(columns=["scaffold"])

    logger.info(f"Scaffold split complete: {len(train_df)} train, {len(test_df)} test samples.")
    logger.info(f"Train scaffolds: {len(train_scaffolds)}, Test scaffolds: {n_scaffolds - len(train_scaffolds)}")

    return train_df, test_df


def split_indices(
    df: pd.DataFrame,
    smiles_col: str = "smiles",
    train_ratio: float = 0.8,
    seed: int = SEED
) -> Tuple[List[int], List[int]]:
    """
    Return train/test split indices based on scaffold.

    Args:
        df: DataFrame containing SMILES strings.
        smiles_col: Column name containing SMILES strings.
        train_ratio: Fraction of scaffolds for training.
        seed: Random seed.

    Returns:
        Tuple of (train_indices, test_indices).
    """
    train_df, test_df = scaffold_split(df, smiles_col, train_ratio, seed)
    train_indices = train_df.index.tolist()
    test_indices = test_df.index.tolist()
    return train_indices, test_indices