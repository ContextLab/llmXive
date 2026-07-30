"""
T029: Implement logic to compute accuracy and aggregate by stimulus ID, emotion, and flanker count.

This module reads the raw synthetic judgment data (produced by T025/T026/T028),
computes the binary accuracy (correct/incorrect) for each trial, and aggregates
the results by stimulus_id, emotion_label, and flanker_count.

Output:
    data/processed/judgment_aggregates.csv
"""
import os
import sys
import logging
import argparse
from pathlib import Path
import pandas as pd
import numpy as np

# Add project root to path for imports if running as script
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import ensure_directories, get_seed
from analysis.data_loader import load_all_judgments

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def compute_accuracy(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute 'accuracy' column (1.0 if response matches true label, 0.0 otherwise).
    
    Args:
        df: DataFrame with 'true_label' and 'response_label' columns.
    
    Returns:
        DataFrame with added 'accuracy' column.
    """
    if 'true_label' not in df.columns or 'response_label' not in df.columns:
        raise ValueError("Input DataFrame must contain 'true_label' and 'response_label' columns.")
    
    # Ensure string comparison
    df = df.copy()
    df['accuracy'] = (df['true_label'].astype(str) == df['response_label'].astype(str)).astype(float)
    return df

def aggregate_judgments(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate accuracy statistics by stimulus_id, emotion_label, and flanker_count.
    
    Aggregates:
        - total_trials: count of trials
        - mean_accuracy: average accuracy (proportion correct)
        - std_accuracy: standard deviation of accuracy (for binomial, derived from p)
        - num_participants: unique count of participants who saw this stimulus
    
    Args:
        df: DataFrame with 'accuracy', 'stimulus_id', 'emotion_label', 'flanker_count', 'participant_id'.
    
    Returns:
        Aggregated DataFrame.
    """
    required_cols = ['stimulus_id', 'emotion_label', 'flanker_count', 'accuracy', 'participant_id']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns for aggregation: {missing}")
    
    # Group by stimulus and experimental conditions
    grouped = df.groupby(['stimulus_id', 'emotion_label', 'flanker_count']).agg(
        total_trials=('accuracy', 'count'),
        mean_accuracy=('accuracy', 'mean'),
        std_accuracy=('accuracy', 'std'),
        num_participants=('participant_id', 'nunique')
    ).reset_index()
    
    # Handle NaN std for single-trial groups (e.g., if only 1 participant per stimulus in synthetic data)
    # If only 1 trial, std is NaN, but logically it's 0 variance for that single sample or undefined.
    # We'll fill NaN with 0.0 for consistency in downstream analysis, or keep NaN if strict.
    # Standard practice for proportion: if n=1, std is 0 (no variation in single observation).
    grouped['std_accuracy'] = grouped['std_accuracy'].fillna(0.0)
    
    # Sort for readability
    grouped = grouped.sort_values(['emotion_label', 'flanker_count', 'stimulus_id'])
    
    return grouped

def main():
    logger.info("Starting T029: Aggregate Judgments")
    
    # Ensure output directories exist
    ensure_directories()
    output_path = PROJECT_ROOT / "data" / "processed" / "judgment_aggregates.csv"
    
    # Load raw judgments (T028 output)
    # The data_loader module is expected to read from data/interim or data/raw depending on pipeline state
    # Assuming load_all_judgments reads the synthetic pilot data generated in T025/T026
    try:
        df_raw = load_all_judgments()
    except FileNotFoundError as e:
        logger.error(f"Could not find raw judgment data. Ensure T027 (Synthetic Pilot) has run. Error: {e}")
        sys.exit(1)
    
    logger.info(f"Loaded {len(df_raw)} raw judgment records.")
    
    # Step 1: Compute Accuracy
    df_with_acc = compute_accuracy(df_raw)
    
    # Step 2: Aggregate
    df_agg = aggregate_judgments(df_with_acc)
    
    # Step 3: Save
    df_agg.to_csv(output_path, index=False)
    logger.info(f"Aggregated data saved to {output_path}")
    logger.info(f"Summary: {len(df_agg)} unique stimulus-condition combinations processed.")
    
    # Print a sample
    logger.info("Sample output:\n" + df_agg.head().to_string())

if __name__ == "__main__":
    main()
