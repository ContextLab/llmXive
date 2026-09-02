"""
Scaffold-based splitting strategy for molecular datasets.

This module implements a scaffold-aware split to ensure that molecules
sharing the same Bemis-Murcko scaffold are kept together in a single partition.
This prevents data leakage where the model learns from a scaffold in the
training set and is tested on a different molecule with the same scaffold.
"""

from typing import Dict, List, Tuple
import hashlib
import logging

import numpy as np
import pandas as pd
from rdkit import Chem
from rdkit.Chem.Scaffolds import MurckoScaffold

logger = logging.getLogger(__name__)


def get_scaffold(smiles: str) -> str:
    """
    Generate a canonical scaffold string for a given SMILES.

    Uses Bemis-Murcko scaffolding. Returns a canonical SMILES of the scaffold
    or a hash of the input if the scaffold cannot be generated.

    Args:
        smiles: Input SMILES string.

    Returns:
        Canonical SMILES of the scaffold or a unique identifier string.
    """
    if not smiles or not isinstance(smiles, str):
        return "unknown_scaffold"

    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return "invalid_mol"

        scaffold = MurckoScaffold.GetScaffoldForMol(mol)
        if scaffold is None:
            return "no_scaffold"

        # Canonicalize the scaffold SMILES to ensure consistency
        scaffold_smiles = Chem.MolToSmiles(scaffold, isomericSmiles=False)
        return scaffold_smiles

    except Exception as e:
        logger.warning(f"Failed to generate scaffold for {smiles}: {e}")
        return f"error_{hashlib.md5(smiles.encode()).hexdigest()[:8]}"


def scaffold_split(
    data: pd.DataFrame,
    smiles_col: str = "smiles",
    frac_train: float = 0.8,
    frac_val: float = 0.1,
    frac_test: float = 0.1,
    seed: int = 42,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Split a dataset into train, validation, and test sets based on molecular scaffolds.

    Molecules sharing the same scaffold are kept together in the same split to prevent
    data leakage. The split is performed by grouping molecules by their scaffold,
    shuffling the groups, and then assigning them to splits based on the specified fractions.

    Args:
        data: DataFrame containing molecular data. Must have a column specified by `smiles_col`.
        smiles_col: Name of the column containing SMILES strings.
        frac_train: Fraction of data for training.
        frac_val: Fraction of data for validation.
        frac_test: Fraction of data for testing.
        seed: Random seed for reproducibility.

    Returns:
        Tuple of (train_df, val_df, test_df) DataFrames.

    Raises:
        ValueError: If fractions do not sum to 1.0 or if data is empty.
    """
    if not np.isclose(frac_train + frac_val + frac_test, 1.0):
        raise ValueError(
            f"Fractions must sum to 1.0, got {frac_train + frac_val + frac_test}"
        )

    if data.empty:
        raise ValueError("Input data cannot be empty.")

    if smiles_col not in data.columns:
        raise ValueError(f"Column '{smiles_col}' not found in data.")

    logger.info(f"Performing scaffold split on {len(data)} molecules...")

    # Calculate scaffold for each molecule
    scaffolds = data[smiles_col].apply(get_scaffold)
    data_with_scaffolds = data.copy()
    data_with_scaffolds["scaffold"] = scaffolds

    # Group by scaffold
    scaffold_groups = data_with_scaffolds.groupby("scaffold")

    # Get list of unique scaffolds
    unique_scaffolds = list(scaffold_groups.groups.keys())

    # Shuffle scaffolds deterministically
    rng = np.random.default_rng(seed)
    rng.shuffle(unique_scaffolds)

    # Assign scaffolds to splits
    train_scaffolds = []
    val_scaffolds = []
    test_scaffolds = []

    current_count = 0
    total_count = len(data_with_scaffolds)

    target_train = int(total_count * frac_train)
    target_val = int(total_count * frac_val)
    target_test = int(total_count * frac_test)

    for scaffold in unique_scaffolds:
        group_size = len(scaffold_groups.get_group(scaffold))

        if current_count < target_train:
            train_scaffolds.append(scaffold)
            current_count += group_size
        elif current_count < target_train + target_val:
            val_scaffolds.append(scaffold)
            current_count += group_size
        else:
            test_scaffolds.append(scaffold)
            current_count += group_size

    # Filter data by scaffold assignment
    train_df = data_with_scaffolds[
        data_with_scaffolds["scaffold"].isin(train_scaffolds)
    ].drop(columns=["scaffold"])
    val_df = data_with_scaffolds[
        data_with_scaffolds["scaffold"].isin(val_scaffolds)
    ].drop(columns=["scaffold"])
    test_df = data_with_scaffolds[
        data_with_scaffolds["scaffold"].isin(test_scaffolds)
    ].drop(columns=["scaffold"])

    # Log split statistics
    logger.info(f"Scaffold split completed:")
    logger.info(f"  Train: {len(train_df)} molecules ({100*len(train_df)/len(data):.1f}%)")
    logger.info(f"  Val:   {len(val_df)} molecules ({100*len(val_df)/len(data):.1f}%)")
    logger.info(f"  Test:  {len(test_df)} molecules ({100*len(test_df)/len(data):.1f}%)")
    logger.info(f"  Unique scaffolds - Train: {len(train_scaffolds)}, Val: {len(val_scaffolds)}, Test: {len(test_scaffolds)}")

    return train_df, val_df, test_df


def balanced_scaffold_split(
    data: pd.DataFrame,
    smiles_col: str = "smiles",
    label_col: str = None,
    frac_train: float = 0.8,
    frac_val: float = 0.1,
    frac_test: float = 0.1,
    seed: int = 42,
    n_bins: int = 10,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Perform a scaffold split that attempts to balance the distribution of a target label
    across splits (e.g., reaction rate, pKa).

    This is useful when the target property is correlated with scaffold complexity.
    It groups scaffolds by the average value of the label within that scaffold,
    then assigns groups to ensure the mean label distribution is similar across splits.

    Args:
        data: DataFrame containing molecular data.
        smiles_col: Name of the column containing SMILES strings.
        label_col: Name of the column containing the target label for balancing.
        frac_train: Fraction of data for training.
        frac_val: Fraction of data for validation.
        frac_test: Fraction of data for testing.
        seed: Random seed for reproducibility.
        n_bins: Number of bins to use for stratifying the label distribution.

    Returns:
        Tuple of (train_df, val_df, test_df) DataFrames.
    """
    if label_col is not None and label_col not in data.columns:
        raise ValueError(f"Label column '{label_col}' not found in data.")

    if data.empty:
        raise ValueError("Input data cannot be empty.")

    logger.info(f"Performing balanced scaffold split on {len(data)} molecules...")

    # Calculate scaffold and average label per scaffold
    data_with_scaffolds = data.copy()
    data_with_scaffolds["scaffold"] = data_with_scaffolds[smiles_col].apply(get_scaffold)

    scaffold_stats = data_with_scaffolds.groupby("scaffold").agg({
        "scaffold": "first",
        "smiles": "count"
    }).rename(columns={"smiles": "count"})

    if label_col is not None:
        scaffold_stats["avg_label"] = data_with_scaffolds.groupby("scaffold")[label_col].mean()
        # Bin the average labels
        scaffold_stats["label_bin"] = pd.qcut(
            scaffold_stats["avg_label"].fillna(0),
            q=n_bins,
            duplicates="drop",
            labels=False
        )
    else:
        scaffold_stats["label_bin"] = 0  # All in one bin if no label

    # Get unique scaffolds grouped by bin
    unique_bins = scaffold_stats["label_bin"].unique()
    rng = np.random.default_rng(seed)

    train_scaffolds = []
    val_scaffolds = []
    test_scaffolds = []

    total_molecules = len(data_with_scaffolds)
    target_train = int(total_molecules * frac_train)
    target_val = int(total_molecules * frac_val)

    current_train = 0
    current_val = 0

    # Process each bin to ensure balance
    for bin_id in unique_bins:
        bin_scaffolds = scaffold_stats[scaffold_stats["label_bin"] == bin_id].index.tolist()
        rng.shuffle(bin_scaffolds)

        for scaffold in bin_scaffolds:
            count = scaffold_stats.loc[scaffold, "count"]

            if current_train < target_train:
                train_scaffolds.append(scaffold)
                current_train += count
            elif current_val < target_val:
                val_scaffolds.append(scaffold)
                current_val += count
            else:
                test_scaffolds.append(scaffold)

    # Filter data
    train_df = data_with_scaffolds[
        data_with_scaffolds["scaffold"].isin(train_scaffolds)
    ].drop(columns=["scaffold"])
    val_df = data_with_scaffolds[
        data_with_scaffolds["scaffold"].isin(val_scaffolds)
    ].drop(columns=["scaffold"])
    test_df = data_with_scaffolds[
        data_with_scaffolds["scaffold"].isin(test_scaffolds)
    ].drop(columns=["scaffold"])

    logger.info(f"Balanced scaffold split completed:")
    logger.info(f"  Train: {len(train_df)} molecules")
    logger.info(f"  Val:   {len(val_df)} molecules")
    logger.info(f"  Test:  {len(test_df)} molecules")

    if label_col is not None:
        for name, df in [("Train", train_df), ("Val", val_df), ("Test", test_df)]:
            mean_val = df[label_col].mean()
            std_val = df[label_col].std()
            logger.info(f"  {name} {label_col}: mean={mean_val:.4f}, std={std_val:.4f}")

    return train_df, val_df, test_df