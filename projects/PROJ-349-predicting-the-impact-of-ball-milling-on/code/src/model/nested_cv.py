import logging
from typing import List, Tuple, Optional
import numpy as np
import pandas as pd
from sklearn.model_selection import KFold, StratifiedKFold
from src.utils.logger import get_module_logger
from src.utils.seed import get_seed

logger = get_module_logger(__name__)

def generate_splits(
    df: pd.DataFrame,
    target_col: str = "d50",
    n_splits: int = 5,
    n_repeats: int = 3,
    random_state: Optional[int] = None
) -> List[Tuple[np.ndarray, np.ndarray]]:
    """
    Generate stratified train/test splits based on the target column (D50).
    
    Implements a fallback mechanism for when pandas.qcut fails due to insufficient
    unique values (ties). It reduces the number of bins (q) by half (10 -> 5 -> 2)
    until a valid split is possible. If q=1 is reached, it logs a warning and
    falls back to a standard random split without stratification.
    
    Args:
        df: Input DataFrame.
        target_col: Name of the target column to stratify by.
        n_splits: Number of splits (k) for KFold.
        n_repeats: Number of repeats for the split generation.
        random_state: Seed for reproducibility.
        
    Returns:
        List of (train_indices, test_indices) tuples.
    """
    if random_state is None:
        random_state = get_seed()
        
    np.random.seed(random_state)
    
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in DataFrame.")
        
    y = df[target_col].values
    n_samples = len(y)
    
    if n_samples < n_splits:
        raise ValueError(f"Number of samples ({n_samples}) is less than n_splits ({n_splits}).")
    
    splits = []
    
    # Strategy: Try stratification with decreasing bin counts
    # Start with 10 bins, then 5, then 2. If all fail, fallback to random.
    bin_attempts = [10, 5, 2]
    stratified_success = False
    
    for q in bin_attempts:
        try:
            # Attempt quantile binning
            # We need at least q unique values to have q bins
            if len(np.unique(y)) < q:
                logger.debug(f"Skipping q={q}: Insufficient unique values ({len(np.unique(y))}).")
                continue
            
            # Use qcut to create bins
            # labels=False returns integer labels for each bin
            bins = pd.qcut(y, q=q, labels=False, duplicates='drop')
            
            # If duplicates='drop' reduced the number of bins below q, we might still be okay
            # but if it results in only 1 bin, we can't stratify meaningfully for >1 split
            n_unique_bins = len(np.unique(bins))
            if n_unique_bins < 2:
                logger.debug(f"Skipping q={q}: Binning resulted in too few unique bins ({n_unique_bins}).")
                continue
            
            # Create StratifiedKFold
            # Ensure n_splits <= n_unique_bins
            effective_splits = min(n_splits, n_unique_bins)
            
            skf = StratifiedKFold(n_splits=effective_splits, shuffle=True, random_state=random_state)
            
            for _ in range(n_repeats):
                for train_idx, test_idx in skf.split(np.zeros(n_samples), bins):
                    splits.append((train_idx, test_idx))
                    
            stratified_success = True
            logger.info(f"Stratified splits generated successfully with q={q} bins.")
            break # Success, stop trying lower q values
            
        except ValueError as e:
            # qcut might raise ValueError if bins are not well-defined
            logger.debug(f"qcut failed for q={q}: {e}")
            continue
        except Exception as e:
            logger.warning(f"Unexpected error during stratification with q={q}: {e}")
            continue

    if not stratified_success:
        logger.warning("Stratification disabled: insufficient unique values.")
        logger.info("Falling back to standard random split (no stratification).")
        
        # Fallback: Standard KFold (Random Split)
        kf = KFold(n_splits=n_splits, shuffle=True, random_state=random_state)
        
        for _ in range(n_repeats):
            for train_idx, test_idx in kf.split(np.zeros(n_samples)):
                splits.append((train_idx, test_idx))
                
    return splits

def generate_nested_splits(
    df: pd.DataFrame,
    target_col: str = "d50",
    outer_splits: int = 5,
    inner_splits: int = 3,
    n_repeats: int = 3,
    random_state: Optional[int] = None
) -> List[Tuple[List[Tuple[np.ndarray, np.ndarray]], Tuple[np.ndarray, np.ndarray]]]:
    """
    Generate nested cross-validation splits.
    
    Returns a list where each item corresponds to one outer fold (repeated).
    Each item is a tuple: (list_of_inner_splits, (outer_train_idx, outer_test_idx))
    
    The inner splits are generated from the outer training set.
    """
    if random_state is None:
        random_state = get_seed()
        
    outer_split_generators = generate_splits(
        df, 
        target_col=target_col, 
        n_splits=outer_splits, 
        n_repeats=n_repeats, 
        random_state=random_state
    )
    
    nested_results = []
    
    # We need to iterate through the outer splits generated
    # Note: generate_splits returns a flat list of (train, test) for all repeats.
    # We need to group them by repeat to form the outer loop properly, 
    # or simply treat every (train, test) as an outer fold.
    # Given the structure of generate_splits, we treat every returned pair as an outer fold.
    
    # However, for nested CV, we usually want to ensure the inner splits 
    # are consistent for a specific outer training set.
    # Let's iterate through the outer splits.
    
    for outer_train_idx, outer_test_idx in outer_split_generators:
        outer_train_df = df.iloc[outer_train_idx]
        
        # Generate inner splits for the training set only
        # We use the same logic but on the subset
        inner_split_generators = generate_splits(
            outer_train_df,
            target_col=target_col,
            n_splits=inner_splits,
            n_repeats=1, # Usually 1 repeat for inner loop in nested CV to save time, 
                         # or match outer repeats if specified. Spec says "Repeated Nested".
                         # Let's stick to 1 repeat for inner to keep complexity manageable 
                         # unless n_repeats > 1 is specifically requested for inner too.
                         # The task description implies reusing the same logic.
            random_state=random_state + 1 # Offset seed for inner
        )
        
        inner_splits_list = []
        for inner_train_rel_idx, inner_test_rel_idx in inner_split_generators:
            # Map relative indices back to absolute indices
            # outer_train_idx contains the absolute indices for the outer train set
            # inner_train_rel_idx are indices into outer_train_df
            
            absolute_inner_train_idx = outer_train_idx[inner_train_rel_idx]
            absolute_inner_test_idx = outer_train_idx[inner_test_rel_idx]
            
            inner_splits_list.append((absolute_inner_train_idx, absolute_inner_test_idx))
        
        nested_results.append((inner_splits_list, (outer_train_idx, outer_test_idx)))
        
    return nested_results
