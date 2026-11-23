"""
T008d: Merge Ground Truth Utility (Training)

Logic: Join ablation_labels_train.json with metrics_with_moves.csv to produce
data/processed/ground_truth_utility_train.csv (columns include utility_delta).

Dependencies:
- data/processed/ablation_labels_train.json (from T008)
- data/processed/metrics_with_moves.csv (from T006a)

Output:
- data/processed/ground_truth_utility_train.csv
"""
import os
import sys
import json
import logging
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/processed/t008d_merge_ground_truth.log')
    ]
)
logger = logging.getLogger(__name__)

# Define paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ABALATION_LABELS_PATH = PROJECT_ROOT / 'data' / 'processed' / 'ablation_labels_train.json'
METRICS_PATH = PROJECT_ROOT / 'data' / 'processed' / 'metrics_with_moves.csv'
OUTPUT_PATH = PROJECT_ROOT / 'data' / 'processed' / 'ground_truth_utility_train.csv'

def load_ablation_labels(path: Path) -> List[Dict[str, Any]]:
    """Load ablation labels from JSON file."""
    if not path.exists():
        raise FileNotFoundError(f"Ablation labels file not found: {path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if not isinstance(data, list):
        raise ValueError(f"Expected list in {path}, got {type(data)}")
    
    logger.info(f"Loaded {len(data)} ablation labels from {path}")
    return data

def load_metrics(path: Path) -> pd.DataFrame:
    """Load metrics with moves from CSV file."""
    if not path.exists():
        raise FileNotFoundError(f"Metrics file not found: {path}")
    
    df = pd.read_csv(path)
    logger.info(f"Loaded {len(df)} rows from {path}")
    return df

def merge_ground_truth(ablation_labels: List[Dict[str, Any]], metrics_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge ablation labels with metrics to create ground truth utility dataset.
    
    The ablation labels contain:
    - trajectory_id
    - utility_delta (baseline_win_rate - ablated_win_rate)
    
    The metrics contain:
    - trajectory_id, turn, health_ratio, enemy_threat, deck_size, move_entropy, layer_name
    
    We merge on trajectory_id to associate utility_delta with the corresponding metrics.
    """
    # Convert ablation labels to DataFrame
    ablation_df = pd.DataFrame(ablation_labels)
    
    # Validate required columns in ablation labels
    required_ablation_cols = ['trajectory_id', 'utility_delta']
    missing_cols = [col for col in required_ablation_cols if col not in ablation_df.columns]
    if missing_cols:
        raise ValueError(f"Ablation labels missing required columns: {missing_cols}")
    
    # Validate required columns in metrics
    if 'trajectory_id' not in metrics_df.columns:
        raise ValueError("Metrics file missing 'trajectory_id' column")
    
    # Merge on trajectory_id
    # Use 'inner' join to keep only trajectories that exist in both datasets
    merged_df = pd.merge(
        ablation_df[['trajectory_id', 'utility_delta']],
        metrics_df,
        on='trajectory_id',
        how='inner'
    )
    
    logger.info(f"Merged dataset has {len(merged_df)} rows")
    logger.info(f"Columns in merged dataset: {list(merged_df.columns)}")
    
    # Ensure utility_delta is numeric
    merged_df['utility_delta'] = pd.to_numeric(merged_df['utility_delta'], errors='coerce')
    
    # Log any NaN values in utility_delta
    nan_count = merged_df['utility_delta'].isna().sum()
    if nan_count > 0:
        logger.warning(f"Found {nan_count} NaN values in utility_delta after merge")
    
    return merged_df

def validate_output(df: pd.DataFrame) -> bool:
    """Validate the output DataFrame."""
    required_cols = ['trajectory_id', 'utility_delta']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        logger.error(f"Output missing required columns: {missing_cols}")
        return False
    
    if len(df) == 0:
        logger.error("Output DataFrame is empty")
        return False
    
    # Check for NaN in utility_delta
    if df['utility_delta'].isna().any():
        logger.warning("Output contains NaN values in utility_delta column")
    
    logger.info("Output validation passed")
    return True

def main():
    """Main entry point for T008d."""
    logger.info("Starting T008d: Merge Ground Truth Utility (Training)")
    
    try:
        # Ensure output directory exists
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        
        # Load input data
        logger.info(f"Loading ablation labels from {ABALATION_LABELS_PATH}")
        ablation_labels = load_ablation_labels(ABALATION_LABELS_PATH)
        
        logger.info(f"Loading metrics from {METRICS_PATH}")
        metrics_df = load_metrics(METRICS_PATH)
        
        # Merge datasets
        logger.info("Merging datasets...")
        merged_df = merge_ground_truth(ablation_labels, metrics_df)
        
        # Validate output
        if not validate_output(merged_df):
            raise ValueError("Output validation failed")
        
        # Save output
        logger.info(f"Saving merged ground truth to {OUTPUT_PATH}")
        merged_df.to_csv(OUTPUT_PATH, index=False)
        
        logger.info(f"T008d completed successfully. Output: {OUTPUT_PATH}")
        logger.info(f"Output shape: {merged_df.shape}")
        logger.info(f"Sample of utility_delta values: {merged_df['utility_delta'].head(10).tolist()}")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise

if __name__ == '__main__':
    main()