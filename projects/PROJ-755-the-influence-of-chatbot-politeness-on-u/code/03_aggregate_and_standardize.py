"""
T019: Implement aggregation logic to compute mean_politeness_score per dialogue
and z-score standardization.

This script loads the scored dialogues from T018, aggregates utterance-level
politeness scores to the dialogue level, and applies z-score standardization.

Output: data/processed/scored_dialogues.parquet
"""
import os
import sys
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd
import numpy as np

# Ensure the code directory is in the path for imports
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def ensure_directories(output_path: Path) -> None:
    """Ensure the output directory exists."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured output directory exists: {output_path.parent}")

def load_scored_dialogues(input_path: Path) -> pd.DataFrame:
    """
    Load the scored dialogues DataFrame.
    
    Expected columns: dialogue_id, utterance_id, politeness_score, quality_rating, user_id
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    logger.info(f"Loading scored dialogues from {input_path}")
    df = pd.read_parquet(input_path)
    
    required_cols = ['dialogue_id', 'politeness_score']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in input: {missing_cols}")
    
    logger.info(f"Loaded {len(df)} utterances with columns: {list(df.columns)}")
    return df

def aggregate_dialogue_scores(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate utterance-level politeness scores to the dialogue level.
    
    Computes:
    - mean_politeness_score: Mean of politeness_score per dialogue_id
    - count_utterances: Number of utterances per dialogue
    - std_politeness_score: Standard deviation of politeness_score per dialogue
    
    Returns a DataFrame with one row per dialogue.
    """
    logger.info("Aggregating utterance scores to dialogue level...")
    
    agg_df = df.groupby('dialogue_id').agg(
        mean_politeness_score=('politeness_score', 'mean'),
        count_utterances=('politeness_score', 'count'),
        std_politeness_score=('politeness_score', 'std')
    ).reset_index()
    
    # Handle dialogues with only one utterance (std will be NaN)
    agg_df['std_politeness_score'] = agg_df['std_politeness_score'].fillna(0)
    
    logger.info(f"Aggregated to {len(agg_df)} dialogues")
    logger.info(f"Aggregated columns: {list(agg_df.columns)}")
    
    return agg_df

def standardize_scores(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply z-score standardization to mean_politeness_score.
    
    Formula: z = (x - mean) / std
    Handles edge cases where std is 0 or NaN.
    
    Adds column: z_politeness_score
    """
    logger.info("Applying z-score standardization...")
    
    mean_val = df['mean_politeness_score'].mean()
    std_val = df['mean_politeness_score'].std()
    
    if pd.isna(std_val) or std_val == 0:
        logger.warning("Standard deviation is 0 or NaN; cannot standardize. Setting all z-scores to 0.")
        df['z_politeness_score'] = 0.0
    else:
        df['z_politeness_score'] = (df['mean_politeness_score'] - mean_val) / std_val
    
    logger.info(f"Standardization complete. Mean z-score: {df['z_politeness_score'].mean():.6f}, Std: {df['z_politeness_score'].std():.6f}")
    
    return df

def save_results(df: pd.DataFrame, output_path: Path) -> None:
    """
    Save the aggregated and standardized results to a Parquet file.
    
    Final columns include:
    - dialogue_id
    - mean_politeness_score
    - count_utterances
    - std_politeness_score
    - z_politeness_score
    - quality_rating (if present in input, propagated)
    - user_id (if present in input, propagated)
    """
    logger.info(f"Saving results to {output_path}")
    
    # Ensure output directory exists
    ensure_directories(output_path)
    
    df.to_parquet(output_path, index=False)
    logger.info(f"Successfully saved {len(df)} dialogues to {output_path}")
    
    # Log summary statistics
    logger.info(f"Output columns: {list(df.columns)}")
    logger.info(f"Mean politeness score: {df['mean_politeness_score'].mean():.4f} (std: {df['mean_politeness_score'].std():.4f})")
    logger.info(f"Z-score mean: {df['z_politeness_score'].mean():.6f}, Z-score std: {df['z_politeness_score'].std():.6f}")

def main():
    parser = argparse.ArgumentParser(description="Aggregate and standardize politeness scores per dialogue.")
    parser.add_argument(
        "--input", 
        type=str, 
        default="data/processed/scored_dialogues_raw.parquet",
        help="Path to input scored dialogues file (output from T018)"
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default="data/processed/scored_dialogues.parquet",
        help="Path to output aggregated and standardized file"
    )
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    try:
        # Load data
        df = load_scored_dialogues(input_path)
        
        # Aggregate to dialogue level
        agg_df = aggregate_dialogue_scores(df)
        
        # Merge back any dialogue-level metadata (quality_rating, user_id) if present in original
        # Assuming original df has these at utterance level, we take the first occurrence per dialogue
        metadata_cols = [col for col in df.columns if col not in ['dialogue_id', 'utterance_id', 'politeness_score']]
        if metadata_cols:
            logger.info(f"Merging metadata columns: {metadata_cols}")
            meta_df = df[['dialogue_id'] + metadata_cols].drop_duplicates(subset=['dialogue_id'])
            agg_df = agg_df.merge(meta_df, on='dialogue_id', how='left')
        
        # Standardize
        final_df = standardize_scores(agg_df)
        
        # Save results
        save_results(final_df, output_path)
        
        logger.info("T019 completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Input file not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during aggregation: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
