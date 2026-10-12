"""
Scaffold‑based train/test splitter.

The implementation uses RDKit's Murcko scaffold to assign each molecule to a
scaffold group.  Whole scaffold groups are placed either in the training set
or the test set – this prevents molecules that share a core scaffold from
leaking between splits.
"""

import argparse
import logging
import random
from pathlib import Path
from typing import Tuple, List

import pandas as pd
from rdkit import Chem
from rdkit.Chem.Scaffolds import MurckoScaffold

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def _murcko_scaffold(smiles: str) -> str | None:
    """Return the Murcko scaffold SMILES for a given molecule."""
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    scaffold = MurckoScaffold.GetScaffoldForMol(mol)
    if scaffold is None:
        return None
    return Chem.MolToSmiles(scaffold, isomericSmiles=True)

def assign_scaffolds(df: pd.DataFrame, smiles_col: str = "smiles") -> pd.DataFrame:
    """Add a ``scaffold_id`` column to the DataFrame."""
    if smiles_col not in df.columns:
        raise ValueError(f"'{smiles_col}' column not found in DataFrame.")
    df = df.copy()
    df["scaffold_id"] = df[smiles_col].apply(_murcko_scaffold)
    return df

def scaffold_split(
    df: pd.DataFrame,
    test_fraction: float = 0.2,
    seed: int = 42,
    smiles_col: str = "smiles",
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split a DataFrame into train / test sets based on scaffold groups.

    Parameters
    ----------
    df : pd.DataFrame
        Input data containing at least a ``smiles`` column.
    test_fraction : float, default 0.2
        Approximate fraction of molecules to allocate to the test set.
    seed : int, default 42
        Random seed for reproducibility.
    smiles_col : str, default "smiles"
        Name of the column containing SMILES strings.

    Returns
    -------
    train_df, test_df : Tuple[pd.DataFrame, pd.DataFrame]
        DataFrames for training and testing.
    """
    random.seed(seed)
    df = assign_scaffolds(df, smiles_col=smiles_col)

    # Group rows by scaffold
    scaffold_groups = df.groupby("scaffold_id")
    scaffold_ids = list(scaffold_groups.groups.keys())
    random.shuffle(scaffold_ids)

    n_total = len(df)
    n_test_target = int(n_total * test_fraction)

    test_ids: List[str] = []
    n_test = 0
    for scaf in scaffold_ids:
        group_size = len(scaffold_groups.get_group(scaf))
        if n_test + group_size <= n_test_target or not test_ids:
            test_ids.append(scaf)
            n_test += group_size
        if n_test >= n_test_target:
            break

    test_mask = df["scaffold_id"].isin(test_ids)
    test_df = df[test_mask].drop(columns=["scaffold_id"])
    train_df = df[~test_mask].drop(columns=["scaffold_id"])
    return train_df, test_df

def _save_split(train_df: pd.DataFrame, test_df: pd.DataFrame) -> None:
    """Write the split CSV files to the standard processed data folder."""
    out_dir = paths.data("processed")
    out_dir.mkdir(parents=True, exist_ok=True)
    train_path = out_dir / "train.csv"
    test_path = out_dir / "test.csv"
    train_df.to_csv(train_path, index=False)
    test_path.to_csv(test_path, index=False)
    log.info(f"Train split written to {train_path}")
    log.info(f"Test split written to {test_path}")

def _parse_cli() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scaffold‑based train/test split for molecular data."
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to the CSV file containing at least a 'smiles' column.",
    )
    parser.add_argument(
        "--test-fraction",
        type=float,
        default=0.2,
        help="Fraction of data to allocate to the test set (default 0.2).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default 42).",
    )
    return parser.parse_args()

def main() -> int:
    args = _parse_cli()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    try:
        df = pd.read_csv(args.input)
    except Exception as exc:
        log.error(f"Failed to read input CSV '{args.input}': {exc}")
        return 1

    train_df, test_df = scaffold_split(
        df,
        test_fraction=args.test_fraction,
        seed=args.seed,
    )
    _save_split(train_df, test_df)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
