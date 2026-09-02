"""
Splitting module for stratified scaffold-based data partitioning.

Implements:
1. Grouping by reaction_class and scaffold_id
2. Stratified split of groups by reaction_class
3. Assignment of all members of a scaffold group to the same split
4. Edge case handling for small classes
5. Output generation with validation

Outputs:
- data/processed/stratified_groups.csv
- data/results/split_log.json
- data/processed/validation_set_indices.csv
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Constants
RANDOM_SEED = 42
TRAIN_RATIO = 0.7
VAL_RATIO = 0.15
TEST_RATIO = 0.15
MIN_CLASS_SIZE = 5  # Minimum reactions per class to include in stratification

def get_scaffold_group_keys(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate scaffold group keys from the cleaned reactions dataframe.
    
    Args:
        df: DataFrame with columns: smiles, yield, reaction_class, 
            fingerprint_ecfp, fingerprint_maccs, scaffold_id (from T010)
    
    Returns:
        DataFrame with scaffold_id and reaction_class grouped appropriately
    """
    if 'scaffold_id' not in df.columns:
        logger.error("Input DataFrame must contain 'scaffold_id' column from T010")
        raise ValueError("Missing 'scaffold_id' column")
    
    # Group by reaction_class and scaffold_id
    group_keys = df.groupby(['reaction_class', 'scaffold_id']).size().reset_index(name='count')
    return group_keys

def stratified_scaffold_split(
    df: pd.DataFrame, 
    group_keys: pd.DataFrame,
    train_ratio: float = TRAIN_RATIO,
    val_ratio: float = VAL_RATIO,
    test_ratio: float = TEST_RATIO,
    random_seed: int = RANDOM_SEED
) -> Dict[str, pd.DataFrame]:
    """
    Perform stratified split of scaffold groups by reaction_class.
    
    Algorithm:
    1. Group data by reaction_class and scaffold_id
    2. Stratify groups by reaction_class
    3. Assign all members of a scaffold group to the same split
    4. Handle edge cases: classes with only one scaffold (assign to train),
       small classes (merge or exclude with warning)
    
    Args:
        df: Full dataframe with scaffold_id
        group_keys: Grouped dataframe with scaffold_id and reaction_class
        train_ratio: Fraction for training set
        val_ratio: Fraction for validation set
        test_ratio: Fraction for test set
        random_seed: Random seed for reproducibility
    
    Returns:
        Dictionary with 'train', 'val', 'test' dataframes
    """
    logger.info(f"Starting stratified scaffold split with ratios: train={train_ratio}, val={val_ratio}, test={test_ratio}")
    
    # Verify ratios sum to 1
    total_ratio = train_ratio + val_ratio + test_ratio
    if abs(total_ratio - 1.0) > 0.001:
        logger.warning(f"Split ratios sum to {total_ratio}, normalizing...")
        train_ratio /= total_ratio
        val_ratio /= total_ratio
        test_ratio /= total_ratio
    
    # Get unique reaction classes
    reaction_classes = df['reaction_class'].unique()
    logger.info(f"Found {len(reaction_classes)} reaction classes")
    
    # Filter classes with sufficient size
    valid_classes = []
    excluded_classes = []
    for rc in reaction_classes:
        class_count = len(df[df['reaction_class'] == rc])
        if class_count >= MIN_CLASS_SIZE:
            valid_classes.append(rc)
        else:
            excluded_classes.append((rc, class_count))
    
    if excluded_classes:
        logger.warning(f"Excluding {len(excluded_classes)} classes with < {MIN_CLASS_SIZE} reactions:")
        for rc, count in excluded_classes:
            logger.warning(f"  - {rc}: {count} reactions")
    
    # Filter dataframe to valid classes
    df_valid = df[df['reaction_class'].isin(valid_classes)].copy()
    
    if len(df_valid) == 0:
        logger.error("No valid classes with sufficient data")
        raise ValueError("No valid classes with sufficient data")
    
    # Create group identifiers
    df_valid['group_id'] = df_valid['scaffold_id']
    
    # Get unique groups with their reaction classes
    unique_groups = df_valid[['group_id', 'reaction_class']].drop_duplicates()
    unique_groups['group_size'] = df_valid.groupby('group_id').size().reset_index(drop=True)
    
    # Stratified split of groups by reaction_class
    # We need to ensure each scaffold group stays together
    gss = GroupShuffleSplit(
        n_splits=1, 
        test_size=(val_ratio + test_ratio), 
        train_size=train_ratio,
        random_state=random_seed
    )
    
    # Get group labels for stratification (reaction_class)
    group_labels = unique_groups.set_index('group_id')['reaction_class']
    groups = unique_groups['group_id'].values
    
    # Perform split
    train_idx, temp_idx = next(gss.split(groups, group_labels))
    
    train_groups = groups[train_idx]
    temp_groups = groups[temp_idx]
    
    # Split temp into val and test
    if len(temp_groups) > 0:
        # Adjust ratios for the second split
        val_ratio_adj = val_ratio / (val_ratio + test_ratio)
        test_ratio_adj = test_ratio / (val_ratio + test_ratio)
        
        gss2 = GroupShuffleSplit(
            n_splits=1,
            test_size=test_ratio_adj,
            train_size=val_ratio_adj,
            random_state=random_seed
        )
        
        temp_labels = unique_groups.set_index('group_id').loc[temp_groups]['reaction_class'].values
        temp_idx_split = next(gss2.split(temp_groups, temp_labels))
        
        val_groups = temp_groups[temp_idx_split[0]]
        test_groups = temp_groups[temp_idx_split[1]]
    else:
        val_groups = np.array([])
        test_groups = np.array([])
    
    logger.info(f"Split results: train={len(train_groups)} groups, val={len(val_groups)} groups, test={len(test_groups)} groups")
    
    # Create split assignments
    split_map = {}
    for gid in train_groups:
        split_map[gid] = 'train'
    for gid in val_groups:
        split_map[gid] = 'val'
    for gid in test_groups:
        split_map[gid] = 'test'
    
    # Assign splits to dataframe
    df_valid['split'] = df_valid['group_id'].map(split_map)
    
    # Handle edge cases: classes with only one scaffold
    # These should already be handled by GroupShuffleSplit, but let's verify
    for rc in valid_classes:
        rc_groups = unique_groups[unique_groups['reaction_class'] == rc]['group_id'].values
        rc_splits = [split_map.get(g, None) for g in rc_groups]
        if len(set([s for s in rc_splits if s is not None])) == 0:
            # No split assigned, assign to train
            for g in rc_groups:
                split_map[g] = 'train'
            df_valid.loc[df_valid['group_id'].isin(rc_groups), 'split'] = 'train'
            logger.warning(f"Assigned all groups of class {rc} to train (no split assigned)")
    
    # Filter out any rows that didn't get a split (shouldn't happen, but safety check)
    df_valid = df_valid[df_valid['split'].notna()]
    
    # Verify no scaffold_id appears in multiple splits
    split_counts = df_valid.groupby(['group_id', 'split']).size().reset_index(name='count')
    if len(split_counts) != split_counts['group_id'].nunique():
        logger.error("ERROR: Some scaffold groups appear in multiple splits!")
        raise ValueError("Scaffold groups appear in multiple splits")
    
    # Create output dataframes
    train_df = df_valid[df_valid['split'] == 'train'].copy()
    val_df = df_valid[df_valid['split'] == 'val'].copy()
    test_df = df_valid[df_valid['split'] == 'test'].copy()
    
    return {
        'train': train_df,
        'val': val_df,
        'test': test_df
    }

def create_train_val_test_split(
    df: pd.DataFrame,
    output_dir: Path
) -> Dict[str, Any]:
    """
    Main function to create train/val/test splits and generate output files.
    
    Args:
        df: Cleaned reactions dataframe with scaffold_id
        output_dir: Directory for output files
    
    Returns:
        Dictionary with split statistics and file paths
    """
    logger.info(f"Creating train/val/test split for {len(df)} reactions")
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    results_dir = output_dir.parent / 'results'
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # Get group keys
    group_keys = get_scaffold_group_keys(df)
    
    # Perform stratified split
    splits = stratified_scaffold_split(df, group_keys)
    
    # Save stratified_groups.csv
    stratified_groups_path = output_dir / 'stratified_groups.csv'
    groups_output = df[['group_id', 'split', 'reaction_class']].drop_duplicates()
    groups_output.to_csv(stratified_groups_path, index=False)
    logger.info(f"Saved stratified groups to {stratified_groups_path}")
    
    # Save validation_set_indices.csv (strictly held-out)
    val_indices_path = output_dir / 'validation_set_indices.csv'
    val_indices = splits['val'].index.tolist()
    pd.DataFrame({'index': val_indices}).to_csv(val_indices_path, index=False)
    logger.info(f"Saved validation set indices to {val_indices_path}")
    
    # Calculate split ratios
    total_rows = len(df)
    train_rows = len(splits['train'])
    val_rows = len(splits['val'])
    test_rows = len(splits['test'])
    
    split_ratios = {
        'train': round(train_rows / total_rows, 4),
        'val': round(val_rows / total_rows, 4),
        'test': round(test_rows / total_rows, 4),
        'train_rows': train_rows,
        'val_rows': val_rows,
        'test_rows': test_rows,
        'total_rows': total_rows
    }
    
    # Calculate per-class split distribution
    class_distribution = {}
    for rc in df['reaction_class'].unique():
        class_total = len(df[df['reaction_class'] == rc])
        class_train = len(splits['train'][splits['train']['reaction_class'] == rc])
        class_val = len(splits['val'][splits['val']['reaction_class'] == rc])
        class_test = len(splits['test'][splits['test']['reaction_class'] == rc])
        
        class_distribution[rc] = {
            'total': class_total,
            'train': class_train,
            'val': class_val,
            'test': class_test,
            'train_ratio': round(class_train / class_total, 4) if class_total > 0 else 0,
            'val_ratio': round(class_val / class_total, 4) if class_total > 0 else 0,
            'test_ratio': round(class_test / class_total, 4) if class_total > 0 else 0
        }
    
    # Create split log
    split_log = {
        'timestamp': datetime.now().isoformat(),
        'random_seed': RANDOM_SEED,
        'split_ratios': split_ratios,
        'class_distribution': class_distribution,
        'total_scaffold_groups': group_keys['scaffold_id'].nunique(),
        'train_scaffold_groups': splits['train']['scaffold_id'].nunique(),
        'val_scaffold_groups': splits['val']['scaffold_id'].nunique(),
        'test_scaffold_groups': splits['test']['scaffold_id'].nunique()
    }
    
    # Save split log
    split_log_path = results_dir / 'split_log.json'
    with open(split_log_path, 'w') as f:
        json.dump(split_log, f, indent=2)
    logger.info(f"Saved split log to {split_log_path}")
    
    # Verify no scaffold_id appears in multiple splits
    all_splits = pd.concat([splits['train'], splits['val'], splits['test']])
    scaffold_split_counts = all_splits.groupby(['scaffold_id', 'split']).size().reset_index(name='count')
    if len(scaffold_split_counts) != scaffold_split_counts['scaffold_id'].nunique():
        logger.error("VERIFICATION FAILED: Some scaffold groups appear in multiple splits!")
        raise ValueError("Scaffold groups appear in multiple splits")
    
    logger.info("VERIFICATION PASSED: No scaffold groups appear in multiple splits")
    
    return {
        'split_ratios': split_ratios,
        'files': {
            'stratified_groups': str(stratified_groups_path),
            'validation_indices': str(val_indices_path),
            'split_log': str(split_log_path)
        },
        'splits': splits
    }

def extract_validation_set(
    df: pd.DataFrame,
    output_dir: Path
) -> pd.DataFrame:
    """
    Extract the validation set based on previously saved indices.
    
    Args:
        df: Full dataframe
        output_dir: Directory containing validation_set_indices.csv
    
    Returns:
        Validation set dataframe
    """
    val_indices_path = output_dir / 'validation_set_indices.csv'
    if not val_indices_path.exists():
        logger.error(f"Validation indices file not found: {val_indices_path}")
        raise FileNotFoundError(f"Validation indices file not found: {val_indices_path}")
    
    indices_df = pd.read_csv(val_indices_path)
    val_indices = indices_df['index'].tolist()
    val_df = df.loc[val_indices].copy()
    
    logger.info(f"Extracted validation set with {len(val_df)} rows")
    return val_df

def main():
    """Main entry point for the split module."""
    logger.info("Starting stratified scaffold split pipeline")
    
    # Define paths
    project_root = Path(__file__).parent.parent.parent
    input_file = project_root / 'data' / 'processed' / 'cleaned_reactions.parquet'
    output_dir = project_root / 'data' / 'processed'
    
    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        logger.error("Please run T017 (ingest.py) first to generate cleaned_reactions.parquet")
        sys.exit(1)
    
    # Load data
    logger.info(f"Loading data from {input_file}")
    df = pd.read_parquet(input_file)
    logger.info(f"Loaded {len(df)} reactions")
    
    # Verify required columns
    required_columns = ['smiles', 'yield', 'reaction_class', 'scaffold_id']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        logger.error(f"Missing required columns: {missing_columns}")
        sys.exit(1)
    
    # Create splits
    try:
        result = create_train_val_test_split(df, output_dir)
        logger.info("Split pipeline completed successfully")
        logger.info(f"Split ratios: {result['split_ratios']}")
        logger.info(f"Output files: {result['files']}")
    except Exception as e:
        logger.error(f"Split pipeline failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == '__main__':
    main()