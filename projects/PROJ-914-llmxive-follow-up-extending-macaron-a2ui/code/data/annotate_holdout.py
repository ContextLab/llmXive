"""
T015: Create N=50 human-annotated hold-out set for rubric validation (FR-008).

This script samples 50 diverse interaction turns from the raw A2UI-Bench dataset
and outputs them to a CSV file for manual human annotation. It does NOT perform
the annotation itself (that is done by researchers via an external process),
nor does it include validation logic.

Output: data/holdout_set_raw.csv (50 rows, ready for human labeling)
"""
import os
import sys
import argparse
import pandas as pd
from pathlib import Path
from datetime import datetime

# Import from existing project modules
from data.ingest import load_dataset_from_hf
from utils.logging import get_experiment_logger

# Constants
HOLDOUT_SIZE = 50
OUTPUT_DIR = Path("data")
OUTPUT_FILENAME = "holdout_set_raw.csv"
DATASET_NAME = "llmXive/a2ui-bench"  # Real HuggingFace dataset
RANDOM_SEED = 42  # From code/config.py convention

logger = get_experiment_logger("annotate_holdout")


def sample_holdout_set(df: pd.DataFrame, n: int = HOLDOUT_SIZE, seed: int = RANDOM_SEED) -> pd.DataFrame:
    """
    Sample a diverse subset of N rows for human annotation.
    
    Strategy: Stratified sampling by query length and complexity (if available)
    to ensure the holdout set represents the full distribution of the dataset.
    Falls back to random sampling if stratification columns are missing.
    
    Args:
        df: Raw dataframe from A2UI-Bench
        n: Number of samples to draw
        seed: Random seed for reproducibility
    
    Returns:
        DataFrame with N rows, no duplicates, ready for annotation
    """
    if len(df) < n:
        raise ValueError(f"Dataset has {len(df)} rows, cannot sample {n} rows for holdout set.")
    
    # Reset index to ensure clean sampling
    df_reset = df.reset_index(drop=True)
    
    # Check for stratification columns
    strat_cols = []
    if 'complexity' in df_reset.columns:
        strat_cols.append('complexity')
    if 'intent' in df_reset.columns:
        strat_cols.append('intent')
    
    if len(strat_cols) > 0:
        # Stratified sampling to ensure diversity
        sample_df = df_reset.groupby(strat_cols, group_keys=False).apply(
            lambda x: x.sample(n=min(len(x), max(1, int(n * len(x) / len(df_reset)))), random_state=seed)
        ).reset_index(drop=True)
        
        # If we didn't get enough samples, fill with random
        if len(sample_df) < n:
            remaining = n - len(sample_df)
            excluded = df_reset.drop(sample_df.index)
            additional = excluded.sample(n=remaining, random_state=seed)
            sample_df = pd.concat([sample_df, additional], ignore_index=True)
    else:
        # Fallback to simple random sampling
        sample_df = df_reset.sample(n=n, random_state=seed)
    
    # Ensure no duplicates and exactly n rows
    sample_df = sample_df.drop_duplicates().head(n)
    
    if len(sample_df) < n:
        logger.warning(f"Only got {len(sample_df)} unique samples, expected {n}")
    
    return sample_df


def prepare_holdout_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare the holdout dataframe with only necessary columns for annotation.
    
    Args:
        df: Sampled dataframe with raw data
    
    Returns:
        DataFrame with columns: query, context, ground_truth_intent (if exists),
        and a unique annotation_id
    """
    required_cols = []
    available_cols = df.columns.tolist()
    
    # Identify columns needed for annotation
    if 'query' in available_cols:
        required_cols.append('query')
    if 'context' in available_cols:
        required_cols.append('context')
    if 'ground_truth_intent' in available_cols:
        required_cols.append('ground_truth_intent')
    elif 'intent' in available_cols:
        required_cols.append('intent')
    
    # Select available columns
    selected_cols = [col for col in required_cols if col in available_cols]
    
    if len(selected_cols) == 0:
        # Fallback: use all columns if none match expected names
        logger.warning("No expected annotation columns found, using all columns")
        selected_cols = available_cols[:5]  # Limit to first 5 columns
    
    holdout_df = df[selected_cols].copy()
    
    # Add unique annotation ID
    holdout_df.insert(0, 'annotation_id', [f"HOLDOUT_{i:03d}" for i in range(len(holdout_df))])
    
    # Add a placeholder column for human annotators to fill
    holdout_df['ground_truth_label'] = ''  # Empty, to be filled by humans
    holdout_df['complexity_score'] = ''  # Empty, to be filled by humans
    
    return holdout_df


def save_holdout_set(df: pd.DataFrame, output_path: Path) -> None:
    """
    Save the holdout set to CSV for human annotation.
    
    Args:
        df: Prepared holdout dataframe
        output_path: Path to save the CSV file
    """
    df.to_csv(output_path, index=False)
    logger.info(f"Saved holdout set with {len(df)} rows to {output_path}")


def main():
    """
    Main entry point for creating the N=50 holdout set.
    
    Workflow:
    1. Load raw A2UI-Bench dataset from HuggingFace
    2. Sample N=50 diverse rows
    3. Prepare dataframe with annotation-friendly columns
    4. Save to data/holdout_set_raw.csv
    """
    parser = argparse.ArgumentParser(
        description="Create N=50 human-annotated holdout set for rubric validation"
    )
    parser.add_argument(
        "--size",
        type=int,
        default=HOLDOUT_SIZE,
        help=f"Number of rows to sample for holdout set (default: {HOLDOUT_SIZE})"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=OUTPUT_FILENAME,
        help=f"Output filename (default: {OUTPUT_FILENAME})"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=RANDOM_SEED,
        help=f"Random seed for reproducibility (default: {RANDOM_SEED})"
    )
    args = parser.parse_args()
    
    logger.info(f"Starting holdout set creation: size={args.size}, seed={args.seed}")
    
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / args.output
    
    try:
        # Load real dataset from HuggingFace (fails loudly if unavailable)
        logger.info(f"Loading dataset from {DATASET_NAME}...")
        raw_df = load_dataset_from_hf(DATASET_NAME)
        
        if raw_df is None or len(raw_df) == 0:
            raise RuntimeError("Failed to load dataset: empty or None result")
        
        logger.info(f"Loaded {len(raw_df)} rows from dataset")
        
        # Sample holdout set
        sampled_df = sample_holdout_set(raw_df, n=args.size, seed=args.seed)
        logger.info(f"Sampled {len(sampled_df)} rows for holdout set")
        
        # Prepare for annotation
        holdout_df = prepare_holdout_dataframe(sampled_df)
        
        # Save to CSV
        save_holdout_set(holdout_df, output_path)
        
        logger.info("Holdout set creation completed successfully")
        print(f"✓ Holdout set saved to: {output_path}")
        print(f"  Rows: {len(holdout_df)}")
        print(f"  Columns: {list(holdout_df.columns)}")
        
    except Exception as e:
        logger.error(f"Failed to create holdout set: {str(e)}")
        # Re-raise to ensure the script fails loudly (no synthetic fallback)
        raise


if __name__ == "__main__":
    main()
