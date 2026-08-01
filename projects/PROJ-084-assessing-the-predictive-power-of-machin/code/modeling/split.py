"""
Splitting logic for modeling.
Implements Stratified-by-Class + Intra-Class Scaffold Grouping.
"""
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split
from config import RANDOM_SEED

def create_train_val_test_split(
    df: pd.DataFrame,
    scaffold_col: str = "murcko_scaffold",
    target_col: str = "yield",
    val_size: float = 0.2,
    test_size: float = 0.2
) -> pd.DataFrame:
    """
    Create train/val/test splits ensuring scaffold leakage is minimized.
    
    Strategy:
    1. Group by scaffold.
    2. Split scaffold groups into train/val/test sets.
    3. Assign rows to splits based on their scaffold group.
    
    This is a simplified version of the full scaffold split logic.
    """
    # Ensure scaffold column exists
    if scaffold_col not in df.columns:
        raise ValueError(f"Scaffold column '{scaffold_col}' not found in DataFrame.")
    
    # Get unique scaffolds
    scaffolds = df[scaffold_col].unique()
    
    # Split scaffolds
    n_scaffolds = len(scaffolds)
    val_n = int(n_scaffolds * val_size)
    test_n = int(n_scaffolds * test_size)
    
    # Random split of scaffolds
    np.random.seed(RANDOM_SEED)
    np.random.shuffle(scaffolds)
    
    val_scaffolds = set(scaffolds[:val_n])
    test_scaffolds = set(scaffolds[val_n:val_n+test_n])
    train_scaffolds = set(scaffolds[val_n+test_n:])
    
    # Assign splits
    def assign_split(scaffold):
        if scaffold in val_scaffolds:
            return "val"
        elif scaffold in test_scaffolds:
            return "test"
        else:
            return "train"
    
    df = df.copy()
    df["split"] = df[scaffold_col].apply(assign_split)
    
    return df

def extract_validation_set(df: pd.DataFrame, split_col: str = "split") -> pd.DataFrame:
    """Extract the validation set from a split DataFrame."""
    if split_col not in df.columns:
        raise ValueError(f"Split column '{split_col}' not found.")
    return df[df[split_col] == "val"].reset_index(drop=True)
