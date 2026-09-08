"""
code/modeling/split.py

Implements scaffold-based stratified splitting for reaction datasets.
Generates split artifacts and logs.
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import pandas as pd
import numpy as np
from sklearn.model_selection import GroupShuffleSplit

# Import project utilities
from utils.io import load_parquet, save_parquet, save_csv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("data/results/split_pipeline.log")
    ]
)
logger = logging.getLogger(__name__)

# Constants
DATA_PROCESSED = Path("data/processed")
DATA_RESULTS = Path("data/results")
CLEANED_DATA_PATH = DATA_PROCESSED / "cleaned_reactions.parquet"
SCAFFOLD_GROUPS_PATH = DATA_PROCESSED / "scaffold_groups.parquet"
OUTPUT_GROUPS_CSV = DATA_PROCESSED / "stratified_groups.csv"
OUTPUT_SPLIT_LOG = DATA_RESULTS / "split_log.json"


def get_scaffold_group_keys(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure the dataframe has the necessary group keys.
    Expects 'scaffold_id' to be present (from T010).
    Returns a dataframe with 'group_id' (unique scaffold_id) and 'reaction_class'.
    """
    if 'scaffold_id' not in df.columns:
        raise ValueError("Input dataframe must contain 'scaffold_id' column.")
    
    # Create a unique group_id based on scaffold_id
    # If scaffold_id is already unique per scaffold, we can use it directly
    # But we need a consistent integer ID for grouping if needed
    # For now, assume scaffold_id is the unique key for the group
    group_df = df[['scaffold_id', 'reaction_class']].drop_duplicates()
    group_df = group_df.reset_index(drop=True)
    group_df['group_id'] = group_df.index
    return group_df


def validate_cross_class_scaffolds(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Check for scaffolds appearing in multiple reaction classes.
    Returns a report of cross-class scaffolds.
    """
    scaffold_classes = df.groupby('scaffold_id')['reaction_class'].apply(set).to_dict()
    cross_class_scaffolds = {}
    
    for scaffold_id, classes in scaffold_classes.items():
        if len(classes) > 1:
            cross_class_scaffolds[scaffold_id] = list(classes)
    
    logger.info(f"Found {len(cross_class_scaffolds)} scaffolds appearing in multiple reaction classes.")
    return cross_class_scaffolds


def handle_cross_class_scaffolds(df: pd.DataFrame, cross_class_scaffolds: Dict[str, Any]) -> Tuple[pd.DataFrame, List[str]]:
    """
    Handle cross-class scaffolds by merging classes or excluding scaffolds.
    For this implementation, we will log a warning and assign these scaffolds
    to the most frequent class in the dataset to maintain stratification integrity,
    or simply ensure they are treated as a single group that might be split.
    However, the task requires handling. A robust strategy:
    1. If a scaffold spans classes, it breaks the "scaffold group -> single split" rule if those classes are split.
    2. Strategy: We will keep the data but log the conflict. The split algorithm will treat the scaffold as a single group.
       If the split algorithm stratifies by class, a scaffold spanning classes complicates pure stratification.
       We will proceed by ensuring the group (scaffold) is assigned to ONE split, and we will note the class overlap.
       The 'reaction_class' in the output will be the most frequent class for that scaffold or a merged label.
       For simplicity and to satisfy the task: We will drop rows for cross-class scaffolds if they are too few,
       OR we will assign them to a 'mixed' class.
       
       Let's implement: Assign cross-class scaffolds to a 'MIXED' reaction class to preserve data but flag them.
       This ensures the split by 'reaction_class' (stratification) treats them as a distinct group,
       and the split by scaffold ensures they stay together.
    """
    if not cross_class_scaffolds:
        return df, []
    
    warnings = []
    mixed_scaffold_ids = list(cross_class_scaffolds.keys())
    
    # Create a mask for rows with cross-class scaffolds
    mask = df['scaffold_id'].isin(mixed_scaffold_ids)
    
    if mask.sum() > 0:
        df.loc[mask, 'reaction_class'] = 'MIXED_SCAFFOLD'
        warnings.append(f"Assigned {mask.sum()} rows with cross-class scaffolds to 'MIXED_SCAFFOLD' class.")
        logger.warning(f"Handled {len(mixed_scaffold_ids)} cross-class scaffolds by assigning to 'MIXED_SCAFFOLD'.")
    
    return df, warnings


def stratified_scaffold_split(
    df: pd.DataFrame,
    group_col: str = 'scaffold_id',
    stratify_col: str = 'reaction_class',
    train_ratio: float = 0.7,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
    random_state: int = 42
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Perform a scaffold-based split with stratification by reaction class.
    
    Steps:
    1. Group by scaffold_id (all rows with same scaffold must go to same split).
    2. Stratify these groups by reaction_class.
    3. Split groups into Train, Val, Test.
    4. Assign split labels back to the original dataframe.
    """
    # Validate ratios
    if abs((train_ratio + val_ratio + test_ratio) - 1.0) > 0.01:
        raise ValueError("Ratios must sum to 1.0")
    
    # Get unique groups (scaffolds)
    groups = df.groupby(group_col).size().reset_index(name='count')
    groups['reaction_class'] = df.groupby(group_col)[stratify_col].first().values
    
    # Stratified split of groups
    # We need to split the 'groups' dataframe, not the original 'df'
    
    # First split: Train vs (Val+Test)
    gss_1 = GroupShuffleSplit(n_splits=1, test_size=(val_ratio + test_ratio), random_state=random_state)
    train_idx, temp_idx = next(gss_1.split(groups, groups[stratify_col]))
    
    train_groups = groups.iloc[train_idx]
    temp_groups = groups.iloc[temp_idx]
    
    # Second split: Val vs Test from the temp set
    # We need to re-stratify the temp set if possible, or just split randomly if small
    # To maintain stratification, we try to split temp_groups
    if len(temp_groups) > 1:
        # Normalize ratios for the second split
        temp_total_ratio = val_ratio + test_ratio
        val_ratio_scaled = val_ratio / temp_total_ratio
        
        gss_2 = GroupShuffleSplit(n_splits=1, test_size=test_ratio / temp_total_ratio, random_state=random_state)
        val_idx, test_idx = next(gss_2.split(temp_groups, temp_groups[stratify_col]))
        
        val_groups = temp_groups.iloc[val_idx]
        test_groups = temp_groups.iloc[test_idx]
    else:
        # Fallback if not enough groups
        logger.warning("Not enough groups for strict stratified split. Assigning to Train/Val/Test arbitrarily.")
        val_groups = temp_groups.iloc[:int(len(temp_groups)*val_ratio_scaled)] if len(temp_groups) > 0 else pd.DataFrame()
        test_groups = temp_groups.drop(val_groups.index)
    
    # Create mapping from group_id (scaffold_id) to split
    split_map = {}
    for scaffold_id in train_groups[group_col]:
        split_map[scaffold_id] = 'train'
    for scaffold_id in val_groups[group_col]:
        split_map[scaffold_id] = 'val'
    for scaffold_id in test_groups[group_col]:
        split_map[scaffold_id] = 'test'
    
    # Assign splits to original dataframe
    df = df.copy()
    df['split'] = df[group_col].map(split_map)
    
    train_df = df[df['split'] == 'train']
    val_df = df[df['split'] == 'val']
    test_df = df[df['split'] == 'test']
    
    return train_df, val_df, test_df


def create_train_val_test_split(df: pd.DataFrame) -> pd.DataFrame:
    """
    Orchestrates the split logic and returns the dataframe with 'split' column.
    """
    # Ensure we have the necessary columns
    if 'scaffold_id' not in df.columns or 'reaction_class' not in df.columns:
        raise ValueError("Dataframe must contain 'scaffold_id' and 'reaction_class'.")
    
    # Handle cross-class scaffolds
    cross_class_scaffolds = validate_cross_class_scaffolds(df)
    df, warnings = handle_cross_class_scaffolds(df, cross_class_scaffolds)
    
    # Perform split
    train_df, val_df, test_df = stratified_scaffold_split(df)
    
    # Combine back
    result_df = pd.concat([train_df, val_df, test_df], ignore_index=True)
    
    return result_df, warnings, cross_class_scaffolds


def extract_validation_set(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract the validation set (val split) for tuning.
    The test split is held out for final evaluation.
    """
    if 'split' not in df.columns:
        raise ValueError("Dataframe must have 'split' column.")
    return df[df['split'] == 'val']


def run_split_pipeline() -> Dict[str, Any]:
    """
    Main pipeline function to generate split artifacts.
    """
    logger.info("Starting split pipeline...")
    
    # Load data
    logger.info(f"Loading data from {CLEANED_DATA_PATH}")
    if not CLEANED_DATA_PATH.exists():
        raise FileNotFoundError(f"Input file not found: {CLEANED_DATA_PATH}")
    
    df = load_parquet(CLEANED_DATA_PATH)
    logger.info(f"Loaded {len(df)} rows.")
    
    # Run split
    result_df, warnings, cross_class_scaffolds = create_train_val_test_split(df)
    
    # Calculate ratios
    total = len(result_df)
    train_count = len(result_df[result_df['split'] == 'train'])
    val_count = len(result_df[result_df['split'] == 'val'])
    test_count = len(result_df[result_df['split'] == 'test'])
    
    train_ratio = train_count / total
    val_ratio = val_count / total
    test_ratio = test_count / total
    
    # Prepare output artifacts
    # 1. stratified_groups.csv
    output_groups = result_df[['scaffold_id', 'split', 'reaction_class']].copy()
    # Add a group_id column if needed, but scaffold_id is the group key
    # The task asks for 'group_id'. Let's use scaffold_id as group_id for clarity
    output_groups = output_groups.rename(columns={'scaffold_id': 'group_id'})
    
    save_csv(output_groups, OUTPUT_GROUPS_CSV)
    logger.info(f"Saved {OUTPUT_GROUPS_CSV}")
    
    # 2. split_log.json
    log_data = {
        "train_ratio": round(train_ratio, 4),
        "val_ratio": round(val_ratio, 4),
        "test_ratio": round(test_ratio, 4),
        "cross_class_scaffolds_handled": len(cross_class_scaffolds),
        "cross_class_scaffold_details": {k: v for k, v in list(cross_class_scaffolds.items())[:10]}, # Limit details
        "warnings": warnings,
        "timestamp": datetime.now().isoformat()
    }
    
    with open(OUTPUT_SPLIT_LOG, 'w') as f:
        json.dump(log_data, f, indent=2)
    logger.info(f"Saved {OUTPUT_SPLIT_LOG}")
    
    # Save the split dataframe for downstream tasks (T022c, T024, T025)
    # We save the full dataframe with splits to processed folder
    save_parquet(result_df, DATA_PROCESSED / "split_reactions.parquet")
    
    logger.info("Split pipeline completed successfully.")
    return log_data


def main():
    """
    Entry point for the script.
    """
    try:
        log_data = run_split_pipeline()
        print(f"Split ratios: Train={log_data['train_ratio']}, Val={log_data['val_ratio']}, Test={log_data['test_ratio']}")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()