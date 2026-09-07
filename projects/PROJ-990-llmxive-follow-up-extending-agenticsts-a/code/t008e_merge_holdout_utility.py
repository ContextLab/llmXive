"""
T008e: Merge Ground Truth Utility (Hold-out Set)

Logic:
1. Load ablation labels for the hold-out set (T008c output).
2. Load the metrics master file (T006a output: metrics_with_moves.csv).
3. Join them on 'trajectory_id' to produce ground_truth_utility_holdout.csv.
4. Validate that 'utility_delta' exists and is numeric.
5. Write the result to data/processed/ground_truth_utility_holdout.csv.

Dependencies:
- data/processed/ablation_labels_holdout.json (from T008c)
- data/processed/metrics_with_moves.csv (from T006a)
"""

import os
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any

import pandas as pd

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/processed/t008e_merge_holdout_utility.log')
    ]
)
logger = logging.getLogger(__name__)

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"

INPUT_ABOUT_HOLDOUT = DATA_PROCESSED / "ablation_labels_holdout.json"
INPUT_METRICS = DATA_PROCESSED / "metrics_with_moves.csv"
OUTPUT_FILE = DATA_PROCESSED / "ground_truth_utility_holdout.csv"

def load_ablation_labels_holdout() -> List[Dict[str, Any]]:
    """Load the ablation labels for the hold-out set."""
    if not INPUT_ABOUT_HOLDOUT.exists():
        logger.error(f"Input file not found: {INPUT_ABOUT_HOLDOUT}")
        raise FileNotFoundError(f"Required input file missing: {INPUT_ABOUT_HOLDOUT}")

    with open(INPUT_ABOUT_HOLDOUT, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if not isinstance(data, list):
        logger.error(f"Expected list of records in {INPUT_ABOUT_HOLDOUT}, got {type(data)}")
        raise ValueError("Invalid format for ablation_labels_holdout.json")

    logger.info(f"Loaded {len(data)} ablation records from hold-out set.")
    return data

def load_metrics_master() -> pd.DataFrame:
    """Load the master metrics file containing per-turn data."""
    if not INPUT_METRICS.exists():
        logger.error(f"Input file not found: {INPUT_METRICS}")
        raise FileNotFoundError(f"Required input file missing: {INPUT_METRICS}")

    df = pd.read_csv(INPUT_METRICS)
    logger.info(f"Loaded metrics master: {len(df)} rows, columns: {list(df.columns)}")
    return df

def merge_utility_data(ablation_records: List[Dict[str, Any]], metrics_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge ablation labels with metrics.
    
    The ablation records contain:
      - trajectory_id
      - utility_delta (calculated as baseline - ablated)
      - layer_name (optional, depending on T008c granularity)
    
    We join on 'trajectory_id'. Since metrics_df has multiple rows per trajectory (per turn),
    we need to decide how to handle the merge.
    
    Strategy:
    - The utility_delta is a property of the trajectory (aggregated over turns in T008c).
    - We will merge the utility_delta onto the metrics rows.
    - If a trajectory exists in ablation but not in metrics, it will be dropped (inner join).
    - If a trajectory exists in metrics but not in ablation, it will be dropped (inner join).
    """
    
    # Convert ablation records to DataFrame
    ablation_df = pd.DataFrame(ablation_records)
    
    # Ensure required columns exist
    required_cols = ['trajectory_id', 'utility_delta']
    missing_cols = [c for c in required_cols if c not in ablation_df.columns]
    if missing_cols:
        logger.error(f"Ablation records missing required columns: {missing_cols}")
        raise ValueError(f"Ablation records missing columns: {missing_cols}")
    
    # Select only necessary columns for join to avoid duplication if layer_name varies
    ablation_df = ablation_df[['trajectory_id', 'utility_delta']].drop_duplicates()
    
    # Merge
    merged_df = pd.merge(
        metrics_df,
        ablation_df,
        on='trajectory_id',
        how='inner'
    )
    
    logger.info(f"Merged data shape: {merged_df.shape}")
    
    # Validate utility_delta is numeric
    if not pd.api.types.is_numeric_dtype(merged_df['utility_delta']):
        # Attempt to convert
        try:
            merged_df['utility_delta'] = pd.to_numeric(merged_df['utility_delta'], errors='raise')
            logger.info("Converted utility_delta to numeric.")
        except (ValueError, TypeError) as e:
            logger.error(f"utility_delta is not numeric and cannot be converted: {e}")
            raise ValueError("utility_delta column is not numeric.")
    
    return merged_df

def save_output(df: pd.DataFrame, output_path: Path):
    """Save the merged DataFrame to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved merged ground truth utility to: {output_path}")

def main():
    logger.info("Starting T008e: Merge Ground Truth Utility (Hold-out Set)")
    
    try:
        # 1. Load inputs
        ablation_records = load_ablation_labels_holdout()
        metrics_df = load_metrics_master()
        
        # 2. Merge
        merged_df = merge_utility_data(ablation_records, metrics_df)
        
        # 3. Validate output
        if merged_df.empty:
            logger.warning("Merged result is empty. Check if trajectory IDs match between inputs.")
        else:
            logger.info(f"Validation: {len(merged_df['trajectory_id'].unique())} unique trajectories in output.")
            logger.info(f"Sample utility_delta values: {merged_df['utility_delta'].head().tolist()}")
        
        # 4. Save
        save_output(merged_df, OUTPUT_FILE)
        
        logger.info("T008e completed successfully.")
        
    except FileNotFoundError as e:
        logger.critical(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.critical(f"Data validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()