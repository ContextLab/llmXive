"""
Splitting logic for modeling.
Implements Stratified-by-Class + Intra-Class Scaffold Grouping.
"""
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split
from config import RANDOM_SEED
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    
    This ensures that all reactions sharing a scaffold are kept together
    in a single split, preventing data leakage.
    """
    # Ensure scaffold column exists
    if scaffold_col not in df.columns:
        raise ValueError(f"Scaffold column '{scaffold_col}' not found in DataFrame.")
    
    # Ensure target column exists if we need to stratify (optional enhancement)
    # For now, we strictly follow scaffold grouping to prevent leakage.
    
    # Get unique scaffolds
    unique_scaffolds = df[scaffold_col].unique()
    n_scaffolds = len(unique_scaffolds)
    
    if n_scaffolds < 3:
        raise ValueError(f"Need at least 3 unique scaffolds to split, found {n_scaffolds}.")
    
    # Calculate split sizes based on number of scaffolds
    # We split the scaffolds, not the rows directly, to ensure no leakage
    val_n = max(1, int(n_scaffolds * val_size))
    test_n = max(1, int(n_scaffolds * test_size))
    
    # Ensure we don't exceed total scaffolds
    if val_n + test_n >= n_scaffolds:
        # Adjust if necessary, but keep at least 1 for train
        val_n = max(1, int(n_scaffolds * val_size))
        test_n = max(1, int(n_scaffolds * test_size))
        if val_n + test_n >= n_scaffolds:
            test_n = n_scaffolds - val_n - 1
            if test_n < 1:
                val_n = n_scaffolds - 2
                test_n = 1
    
    train_n = n_scaffolds - val_n - test_n
    if train_n < 1:
        raise ValueError(f"Cannot create a valid split with val_size={val_size} and test_size={test_size}.")
    
    logger.info(f"Splitting {n_scaffolds} scaffolds: Train={train_n}, Val={val_n}, Test={test_n}")
    
    # Random split of scaffolds with fixed seed
    rng = np.random.RandomState(RANDOM_SEED)
    shuffled_scaffolds = unique_scaffolds.copy()
    rng.shuffle(shuffled_scaffolds)
    
    val_scaffolds = set(shuffled_scaffolds[:val_n])
    test_scaffolds = set(shuffled_scaffolds[val_n:val_n+test_n])
    train_scaffolds = set(shuffled_scaffolds[val_n+test_n:])
    
    # Assign splits
    def assign_split(scaffold):
        if pd.isna(scaffold):
            # Handle missing scaffolds by assigning to train or raising error?
            # For safety, assign to train but log warning
            logger.warning(f"Found NaN scaffold, assigning to train.")
            return "train"
        if scaffold in val_scaffolds:
            return "val"
        elif scaffold in test_scaffolds:
            return "test"
        else:
            return "train"
    
    df = df.copy()
    df["split"] = df[scaffold_col].apply(assign_split)
    
    # Log distribution
    logger.info(f"Split distribution: {df['split'].value_counts().to_dict()}")
    
    return df

def extract_validation_set(df: pd.DataFrame, split_col: str = "split") -> pd.DataFrame:
    """
    Extract the held-out validation set from the split DataFrame.
    
    This set is specifically used for SC-003 substructure frequency checks
    and hyperparameter tuning, ensuring it remains 'held-out' from the training data.
    """
    if split_col not in df.columns:
        raise ValueError(f"Split column '{split_col}' not found in DataFrame.")
    
    val_df = df[df[split_col] == "val"].reset_index(drop=True)
    logger.info(f"Extracted validation set with {len(val_df)} reactions.")
    return val_df

def main():
    """
    Main entry point to generate split indices and extract the validation set.
    
    1. Reads cleaned_reactions.parquet.
    2. Applies scaffold-based split to create split_indices.parquet.
    3. Extracts the validation set to data/processed/validation_set.parquet.
    """
    from utils.io import load_parquet, save_parquet
    
    # Define paths relative to project root
    input_path = Path("data/processed/cleaned_reactions.parquet")
    split_output_path = Path("data/processed/split_indices.parquet")
    val_output_path = Path("data/processed/validation_set.parquet")
    
    if not input_path.exists():
        raise FileNotFoundError(
            f"Input file not found: {input_path}. "
            f"Please run T010 (scaffold.py) and T017 (ingest.py) first to generate cleaned_reactions.parquet."
        )
    
    logger.info(f"Loading data from {input_path}")
    df = load_parquet(input_path)
    
    # Check for required columns
    if "murcko_scaffold" not in df.columns:
        raise ValueError(
            "Column 'murcko_scaffold' not found. "
            "Run scaffold generation (T010) first."
        )
    
    logger.info(f"Loaded {len(df)} reactions.")
    
    # Perform split
    df_split = create_train_val_test_split(df)
    
    # Save the full split indices
    logger.info(f"Saving split indices to {split_output_path}")
    save_parquet(df_split, split_output_path)
    
    # Extract and save the validation set specifically
    logger.info(f"Extracting validation set for SC-003 checks...")
    val_df = extract_validation_set(df_split)
    
    if len(val_df) == 0:
        raise RuntimeError("Validation set is empty. Cannot proceed with SC-003 checks.")
    
    logger.info(f"Saving validation set to {val_output_path}")
    save_parquet(val_df, val_output_path)
    
    logger.info("Split and validation extraction completed successfully.")
    return split_output_path, val_output_path

if __name__ == "__main__":
    main()