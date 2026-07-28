import os
import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Configure logging for the splitter module
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants for split ratios (Train, Ablation-Train, Validation, Test)
# Based on standard practices and the requirement for a robust validation set
# We aim for: Train (40%), Ablation-Train (20%), Validation (20%), Test (20%)
# Adjusted to ensure Validation has at least 20 samples if total N is sufficient
SPLIT_RATIOS = {
    'train': 0.40,
    'ablation_train': 0.20,
    'validation': 0.20,
    'test': 0.20
}

# Minimum validation set size constraint (FR-006)
MIN_VALIDATION_SIZE = 20

def load_processed_data(input_path: str) -> pd.DataFrame:
    """
    Load the processed metrics CSV from T006.
    
    Args:
        input_path: Path to data/processed/metrics_with_moves.csv
        
    Returns:
        DataFrame with columns: trajectory_id, turn, health_ratio, threat_level, 
        deck_size, move_entropy, and potentially win_rate (if aggregated)
        
    Raises:
        FileNotFoundError: If input file does not exist
        ValueError: If required columns are missing
    """
    logger.info(f"Loading processed data from {input_path}")
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
        
    df = pd.read_csv(input_path)
    
    # Verify required columns exist
    required_cols = ['trajectory_id', 'turn', 'move_entropy']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in input data: {missing_cols}")
        
    # Aggregate to trajectory level if necessary
    # The splitter needs one row per trajectory for stratification
    if df.shape[0] != df['trajectory_id'].nunique():
        logger.info("Aggregating trajectory-level metrics for stratification...")
        # Calculate win_rate per trajectory if available, or derive from other metrics
        # For now, we assume win_rate might be in the data or needs to be derived
        # If win_rate is not present, we might need to derive it from the raw data
        # or use a proxy. For this implementation, we check for it first.
        if 'win_rate' not in df.columns:
            # If win_rate is not present, we cannot stratify by it directly.
            # However, the task specification explicitly requires stratification by win_rate.
            # We assume the upstream T006 or T006a has populated this, or we derive it.
            # Let's assume for this task that the input CSV has a 'win_rate' column 
            # aggregated at the trajectory level. If not, we raise an error.
            # Actually, looking at T006 description: "Output: data/processed/metrics_with_moves.csv"
            # It doesn't explicitly say win_rate is there. But T014a says "Stratification Key: win_rate".
            # This implies the data must be aggregated to trajectory level with win_rate.
            # We will perform the aggregation here if needed, assuming 'win' column exists or similar.
            # If neither exists, we cannot proceed with stratification by win_rate.
            
            # Fallback: If we have a 'result' or 'outcome' column, we can compute win_rate.
            # If not, we might have to assume a proxy or fail.
            # Let's check for common outcome columns
            outcome_cols = [c for c in df.columns if 'win' in c.lower() or 'result' in c.lower()]
            if outcome_cols:
                # Assume binary win/loss (1/0) or similar
                # Group by trajectory_id and compute mean of win column
                win_col = outcome_cols[0]
                agg_df = df.groupby('trajectory_id').agg({
                    'turn': 'max', # max turns
                    'move_entropy': 'mean',
                    win_col: 'mean' # This becomes win_rate
                }).reset_index()
                agg_df.rename(columns={win_col: 'win_rate'}, inplace=True)
                df = agg_df
            else:
                # If no win info, we cannot stratify by win_rate.
                # We will raise an error as per strict requirement.
                raise ValueError("Input data must contain 'win_rate' or an outcome column to stratify by win_rate.")
        else:
            # Aggregate if multiple rows per trajectory
            agg_cols = [c for c in df.columns if c not in ['trajectory_id']]
            df = df.groupby('trajectory_id')[agg_cols].mean().reset_index()
    
    # Ensure we have win_rate column
    if 'win_rate' not in df.columns:
        raise ValueError("Aggregated data must contain 'win_rate' column for stratification.")
        
    # Ensure win_rate is numeric
    df['win_rate'] = pd.to_numeric(df['win_rate'], errors='coerce')
    df = df.dropna(subset=['win_rate'])
    
    logger.info(f"Loaded {len(df)} trajectories for splitting.")
    return df

def stratified_split(df: pd.DataFrame, seed: int = 42) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Perform a stratified split of the data into Train, Ablation-Train, Validation, and Test sets.
    
    Args:
        df: DataFrame with 'trajectory_id' and 'win_rate' columns
        seed: Random seed for reproducibility
        
    Returns:
        Tuple of (train_df, ablation_train_df, validation_df, test_df)
        
    Raises:
        ValueError: If validation set size is less than MIN_VALIDATION_SIZE
    """
    logger.info("Performing stratified split...")
    np.random.seed(seed)
    
    # Stratify by win_rate bins
    # Create bins for stratification to handle continuous win_rate
    n_bins = 5
    try:
        df['win_rate_bin'] = pd.qcut(df['win_rate'], q=n_bins, duplicates='drop')
    except ValueError:
        # If qcut fails (e.g., too few unique values), use equal width bins
        logger.warning("qcut failed, using equal width bins for stratification.")
        df['win_rate_bin'] = pd.cut(df['win_rate'], bins=n_bins)
        
    # Shuffle the dataframe
    df_shuffled = df.sample(frac=1, random_state=seed).reset_index(drop=True)
    
    # Calculate split indices
    n = len(df_shuffled)
    train_end = int(n * SPLIT_RATIOS['train'])
    ablation_end = train_end + int(n * SPLIT_RATIOS['ablation_train'])
    val_end = ablation_end + int(n * SPLIT_RATIOS['validation'])
    
    # Split the data
    train_df = df_shuffled.iloc[:train_end].drop(columns=['win_rate_bin'], errors='ignore')
    ablation_train_df = df_shuffled.iloc[train_end:ablation_end].drop(columns=['win_rate_bin'], errors='ignore')
    validation_df = df_shuffled.iloc[ablation_end:val_end].drop(columns=['win_rate_bin'], errors='ignore')
    test_df = df_shuffled.iloc[val_end:].drop(columns=['win_rate_bin'], errors='ignore')
    
    # Validate split sizes
    logger.info(f"Split sizes - Train: {len(train_df)}, Ablation-Train: {len(ablation_train_df)}, "
                f"Validation: {len(validation_df)}, Test: {len(test_df)}")
                
    if len(validation_df) < MIN_VALIDATION_SIZE:
        raise ValueError(f"Validation set size ({len(validation_df)}) < {MIN_VALIDATION_SIZE} violates FR-006 hard constraint. Cannot proceed.")
        
    return train_df, ablation_train_df, validation_df, test_df

def validate_split(train_df: pd.DataFrame, ablation_train_df: pd.DataFrame, 
                   validation_df: pd.DataFrame, test_df: pd.DataFrame) -> bool:
    """
    Validate that the splits are disjoint and cover the original data.
    
    Returns:
        True if valid, False otherwise
    """
    all_ids = set(train_df['trajectory_id']) | set(ablation_train_df['trajectory_id']) | \
              set(validation_df['trajectory_id']) | set(test_df['trajectory_id'])
              
    total_ids = len(train_df) + len(ablation_train_df) + len(validation_df) + len(test_df)
    
    if len(all_ids) != total_ids:
        logger.error("Overlap detected in splits!")
        return False
        
    logger.info("Split validation passed: No overlap, all IDs accounted for.")
    return True

def save_split_data(train_df: pd.DataFrame, ablation_train_df: pd.DataFrame,
                    validation_df: pd.DataFrame, test_df: pd.DataFrame,
                    output_dir: str, validation_ids: List[str]) -> None:
    """
    Save the split datasets to CSV and the validation IDs to JSON.
    
    Args:
        train_df: Training set DataFrame
        ablation_train_df: Ablation-Train set DataFrame
        validation_df: Validation set DataFrame
        test_df: Test set DataFrame
        output_dir: Directory to save files (data/processed)
        validation_ids: List of trajectory IDs in the validation set
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Define output paths
    paths = {
        'train': os.path.join(output_dir, 'train_set.csv'),
        'ablation_train': os.path.join(output_dir, 'ablation_train_set.csv'),
        'validation': os.path.join(output_dir, 'validation_set.csv'),
        'test': os.path.join(output_dir, 'test_set.csv'),
        'validation_ids': os.path.join(output_dir, 'validation_set_ids.json')
    }
    
    # Save CSVs
    train_df.to_csv(paths['train'], index=False)
    ablation_train_df.to_csv(paths['ablation_train'], index=False)
    validation_df.to_csv(paths['validation'], index=False)
    test_df.to_csv(paths['test'], index=False)
    
    # Save JSON
    with open(paths['validation_ids'], 'w') as f:
        json.dump(validation_ids, f, indent=2)
        
    logger.info(f"Saved split data to {output_dir}")
    logger.info(f"Validation set IDs saved to {paths['validation_ids']}")

def main():
    """
    Main entry point for the splitter task (T014a).
    """
    # Define paths
    input_file = 'data/processed/metrics_with_moves.csv'
    output_dir = 'data/processed'
    
    try:
        # 1. Load data
        df = load_processed_data(input_file)
        
        # 2. Perform stratified split
        train_df, ablation_train_df, validation_df, test_df = stratified_split(df)
        
        # 3. Validate splits
        if not validate_split(train_df, ablation_train_df, validation_df, test_df):
            raise ValueError("Split validation failed. Aborting.")
            
        # 4. Extract validation IDs
        validation_ids = validation_df['trajectory_id'].tolist()
        
        # 5. Save outputs
        save_split_data(train_df, ablation_train_df, validation_df, test_df, 
                        output_dir, validation_ids)
                        
        logger.info("T014a completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Input file missing: {e}")
        raise
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during splitting: {e}")
        raise

if __name__ == '__main__':
    main()
