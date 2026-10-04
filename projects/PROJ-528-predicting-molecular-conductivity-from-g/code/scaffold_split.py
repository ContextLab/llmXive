"""
Scaffold Splitting Utility (T008, T027)

Implements scaffold-based train/test split to ensure structural diversity.
"""

import logging
from typing import Tuple, List, Optional
import pandas as pd
import numpy as np
from rdkit import Chem
from rdkit.Chem.Scaffolds import MurckoScaffold

logger = logging.getLogger(__name__)

def get_murcko_scaffold(smiles: str) -> Optional[str]:
    """
    Extract the Murcko scaffold from a SMILES string.
    Returns the scaffold as a SMILES string, or None if invalid.
    """
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
        scaffold = MurckoScaffold.GetScaffoldForMol(mol)
        return Chem.MolToSmiles(scaffold)
    except Exception as e:
        logger.warning(f"Failed to extract scaffold from '{smiles}': {e}")
        return None

def scaffold_split(df: pd.DataFrame, smiles_col: str = 'smiles',
                   train_frac: float = 0.8, seed: int = 42) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split the DataFrame into train and test sets based on Murcko scaffolds.
    Ensures that molecules with the same scaffold are in the same split.
    """
    if smiles_col not in df.columns:
        raise ValueError(f"Column '{smiles_col}' not found in DataFrame.")

    # Extract scaffolds
    logger.info("Extracting Murcko scaffolds...")
    scaffolds = df[smiles_col].apply(get_murcko_scaffold)
    df_with_scaffolds = df.copy()
    df_with_scaffolds['scaffold'] = scaffolds

    # Remove rows with invalid scaffolds
    valid_mask = df_with_scaffolds['scaffold'].notna()
    df_valid = df_with_scaffolds[valid_mask].reset_index(drop=True)
    dropped_count = len(df_with_scaffolds) - len(df_valid)
    if dropped_count > 0:
        logger.warning(f"Dropped {dropped_count} rows with invalid scaffolds.")

    if len(df_valid) == 0:
        raise ValueError("No valid scaffolds found. Cannot split.")

    # Group by scaffold and assign to train/test
    scaffold_groups = df_valid.groupby('scaffold')
    scaffold_list = list(scaffold_groups.groups.keys())

    # Shuffle scaffolds
    rng = np.random.default_rng(seed)
    rng.shuffle(scaffold_list)

    # Determine split index
    n_scaffolds = len(scaffold_list)
    n_train_scaffolds = int(n_scaffolds * train_frac)
    train_scaffolds = set(scaffold_list[:n_train_scaffolds])
    test_scaffolds = set(scaffold_list[n_train_scaffolds:])

    # Assign splits
    def assign_split(scaffold: str) -> str:
        if scaffold in train_scaffolds:
            return 'train'
        elif scaffold in test_scaffolds:
            return 'test'
        else:
            return 'val'  # Fallback (should not happen)

    df_valid['split'] = df_valid['scaffold'].apply(assign_split)

    # Separate train and test
    train_df = df_valid[df_valid['split'] == 'train'].drop(columns=['scaffold', 'split'])
    test_df = df_valid[df_valid['split'] == 'test'].drop(columns=['scaffold', 'split'])

    logger.info(f"Scaffold split: {len(train_df)} train, {len(test_df)} test")
    return train_df, test_df

def split_indices(df: pd.DataFrame, smiles_col: str = 'smiles',
                  train_frac: float = 0.8, seed: int = 42) -> Tuple[np.ndarray, np.ndarray]:
    """
    Return indices for train and test splits (for sklearn compatibility).
    """
    train_df, test_df = scaffold_split(df, smiles_col, train_frac, seed)
    train_indices = train_df.index.values
    test_indices = test_df.index.values
    return train_indices, test_indices

def main():
    """CLI for testing scaffold split."""
    import argparse
    parser = argparse.ArgumentParser(description="Test scaffold split.")
    parser.add_argument("--input", type=str, required=True, help="Input CSV.")
    parser.add_argument("--output-train", type=str, required=True, help="Output train CSV.")
    parser.add_argument("--output-test", type=str, required=True, help="Output test CSV.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    args = parser.parse_args()

    from code.logging_config import setup_logging
    setup_logging()

    df = pd.read_csv(args.input)
    train_df, test_df = scaffold_split(df, seed=args.seed)
    train_df.to_csv(args.output_train, index=False)
    test_df.to_csv(args.output_test, index=False)
    logger.info(f"Saved train to {args.output_train}, test to {args.output_test}")
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
