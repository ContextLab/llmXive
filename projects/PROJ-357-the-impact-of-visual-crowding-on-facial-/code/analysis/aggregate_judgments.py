import os
import sys
import logging
import argparse
from pathlib import Path
import pandas as pd

from config import ensure_directories, get_seed
from analysis.data_loader import load_all_judgments

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def compute_accuracy(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute accuracy (correct/incorrect) for each trial.
    
    Args:
        df: DataFrame with 'true_label' and 'response_label' columns.
    
    Returns:
        DataFrame with an added 'accuracy' column (1.0 for correct, 0.0 for incorrect).
    """
    if df.empty:
        logger.warning("Input DataFrame is empty.")
        df['accuracy'] = pd.Series(dtype=float)
        return df

    # Ensure columns exist
    required_cols = ['true_label', 'response_label']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns for accuracy computation: {missing_cols}")

    # Compute accuracy: 1.0 if true_label == response_label, else 0.0
    df['accuracy'] = (df['true_label'] == df['response_label']).astype(float)
    return df

def aggregate_judgments(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate accuracy by stimulus ID, emotion, and flanker count.
    
    Args:
        df: DataFrame with 'stimulus_id', 'emotion_label', 'flanker_count', and 'accuracy'.
    
    Returns:
        DataFrame with aggregated accuracy statistics per group.
    """
    if df.empty:
        logger.warning("Input DataFrame is empty, cannot aggregate.")
        return pd.DataFrame()

    # Ensure required columns exist
    group_cols = ['stimulus_id', 'emotion_label', 'flanker_count']
    missing_cols = [col for col in group_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns for aggregation: {missing_cols}")
    
    if 'accuracy' not in df.columns:
        raise ValueError("Missing 'accuracy' column. Run compute_accuracy first.")

    # Aggregate
    agg_df = df.groupby(group_cols).agg(
        mean_accuracy=('accuracy', 'mean'),
        std_accuracy=('accuracy', 'std'),
        count=('accuracy', 'count'),
        min_accuracy=('accuracy', 'min'),
        max_accuracy=('accuracy', 'max')
    ).reset_index()

    # Handle NaN std for single-observation groups
    agg_df['std_accuracy'] = agg_df['std_accuracy'].fillna(0.0)

    logger.info(f"Aggregated {len(df)} trials into {len(agg_df)} groups.")
    return agg_df

def main():
    """
    Main entry point for the aggregate judgments script.
    Reads raw judgments, computes accuracy, aggregates by stimulus/emotion/flanker,
    and writes the result to data/processed/aggregated_judgments.csv.
    """
    parser = argparse.ArgumentParser(description="Aggregate human judgment data by stimulus parameters.")
    parser.add_argument('--input', type=str, default='data/processed/human_judgments.csv',
                        help='Path to the input raw judgments CSV.')
    parser.add_argument('--output', type=str, default='data/processed/aggregated_judgments.csv',
                        help='Path to the output aggregated CSV.')
    parser.add_argument('--seed', type=int, default=42, help='Random seed for reproducibility.')
    
    args = parser.parse_args()
    
    # Set seed
    set_all_seeds(args.seed)
    
    # Ensure output directory exists
    output_path = Path(args.output)
    ensure_directories([output_path.parent])
    
    input_path = Path(args.input)
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)
    
    logger.info(f"Loading judgments from {input_path}...")
    try:
        df = load_all_judgments(input_path)
    except Exception as e:
        logger.error(f"Failed to load judgments: {e}")
        sys.exit(1)
    
    if df.empty:
        logger.error("Loaded judgments DataFrame is empty.")
        sys.exit(1)
    
    logger.info(f"Loaded {len(df)} judgments. Computing accuracy...")
    df_with_acc = compute_accuracy(df)
    
    logger.info("Aggregating by stimulus ID, emotion, and flanker count...")
    agg_df = aggregate_judgments(df_with_acc)
    
    logger.info(f"Writing aggregated results to {output_path}...")
    agg_df.to_csv(output_path, index=False)
    
    logger.info(f"Aggregation complete. {len(agg_df)} groups saved.")
    print(f"Saved aggregated judgments to {output_path}")
    print(f"Columns: {list(agg_df.columns)}")
    print(agg_df.head())

if __name__ == '__main__':
    main()