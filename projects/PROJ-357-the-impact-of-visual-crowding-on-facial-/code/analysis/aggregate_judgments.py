"""
Aggregation logic for human judgment data.

Computes accuracy per trial and aggregates statistics by stimulus ID,
emotion, and flanker count as required by T029.
"""
import os
import sys
import logging
import argparse
from pathlib import Path
import pandas as pd
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def compute_accuracy(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute accuracy (correct/incorrect) for each trial.
    
    Args:
        df: DataFrame with columns 'true_label' and 'response_label'
    
    Returns:
        DataFrame with added 'accuracy' column (1.0 for correct, 0.0 for incorrect)
    """
    if df.empty:
        logger.warning("Empty DataFrame provided to compute_accuracy")
        return df.copy()
    
    # Ensure required columns exist
    required_cols = ['true_label', 'response_label']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Compute accuracy: 1 if response matches true label, 0 otherwise
    df = df.copy()
    df['accuracy'] = (df['true_label'] == df['response_label']).astype(int)
    
    logger.info(f"Computed accuracy for {len(df)} trials")
    return df

def aggregate_judgments(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate accuracy statistics by stimulus ID, emotion, and flanker count.
    
    Args:
        df: DataFrame with columns 'stimulus_id', 'emotion_label', 'flanker_count', 
            and 'accuracy' (computed by compute_accuracy)
    
    Returns:
        DataFrame with aggregated statistics per (stimulus_id, emotion_label, flanker_count) group
    """
    if df.empty:
        logger.warning("Empty DataFrame provided to aggregate_judgments")
        return pd.DataFrame()
    
    # Ensure required columns exist
    required_cols = ['stimulus_id', 'emotion_label', 'flanker_count', 'accuracy']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns for aggregation: {missing_cols}")
    
    # Group by stimulus_id, emotion_label, and flanker_count
    # Compute mean accuracy, count of trials, and standard deviation
    grouped = df.groupby(['stimulus_id', 'emotion_label', 'flanker_count']).agg(
        mean_accuracy=('accuracy', 'mean'),
        trial_count=('accuracy', 'count'),
        std_accuracy=('accuracy', 'std')
    ).reset_index()
    
    # Fill NaN std (when trial_count=1) with 0.0
    grouped['std_accuracy'] = grouped['std_accuracy'].fillna(0.0)
    
    logger.info(f"Aggregated {len(df)} trials into {len(grouped)} unique stimulus groups")
    return grouped

def main():
    """
    Main entry point for the aggregation script.
    
    Usage:
        python code/analysis/aggregate_judgments.py --input data/processed/human_judgments.csv --output data/processed/aggregated_judgments.csv
    """
    parser = argparse.ArgumentParser(description='Aggregate human judgment data by stimulus and condition')
    parser.add_argument('--input', type=str, required=True, 
                      help='Path to input CSV with raw judgments (e.g., data/processed/human_judgments.csv)')
    parser.add_argument('--output', type=str, required=True,
                      help='Path to output CSV with aggregated accuracy statistics')
    parser.add_argument('--log-level', type=str, default='INFO',
                      choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                      help='Logging level')
    
    args = parser.parse_args()
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    # Validate input file exists
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load raw judgments
    logger.info(f"Loading raw judgments from {input_path}")
    try:
        df = pd.read_csv(input_path)
    except Exception as e:
        logger.error(f"Failed to load input file: {e}")
        sys.exit(1)
    
    logger.info(f"Loaded {len(df)} records")
    
    # Compute accuracy per trial
    df_with_accuracy = compute_accuracy(df)
    
    # Aggregate by stimulus ID, emotion, and flanker count
    aggregated_df = aggregate_judgments(df_with_accuracy)
    
    # Save aggregated results
    logger.info(f"Saving aggregated results to {output_path}")
    aggregated_df.to_csv(output_path, index=False)
    
    # Print summary
    logger.info("Aggregation Summary:")
    logger.info(f"  Total trials: {len(df_with_accuracy)}")
    logger.info(f"  Unique stimulus groups: {len(aggregated_df)}")
    logger.info(f"  Overall mean accuracy: {df_with_accuracy['accuracy'].mean():.3f}")
    
    # Save a quick summary JSON for verification
    summary = {
        "total_trials": int(len(df_with_accuracy)),
        "unique_stimulus_groups": int(len(aggregated_df)),
        "overall_mean_accuracy": float(df_with_accuracy['accuracy'].mean()),
        "overall_std_accuracy": float(df_with_accuracy['accuracy'].std())
    }
    
    summary_path = output_path.with_suffix('.json')
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    logger.info(f"Saved summary to {summary_path}")
    
    print(f"Aggregation complete. Output: {output_path}")
    print(f"Summary: {summary}")

if __name__ == '__main__':
    main()
