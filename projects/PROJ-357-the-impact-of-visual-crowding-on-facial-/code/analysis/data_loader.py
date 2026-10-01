"""
Data Loader Module for Human Judgments

Loads and validates raw pilot response data, computes accuracy,
and aggregates results by stimulus and condition.
"""

import os
import sys
import json
import logging
import pandas as pd
from pathlib import Path
import argparse

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import ensure_directories

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_raw_judgments(file_path):
    """
    Load raw pilot judgment data from CSV.

    Args:
        file_path (str): Path to the raw pilot responses CSV.

    Returns:
        pd.DataFrame: DataFrame containing raw judgments.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Raw pilot data file not found: {file_path}")
    
    logger.info(f"Loading raw judgments from {file_path}")
    df = pd.read_csv(file_path)
    
    required_cols = ['participant_id', 'stimulus_id', 'true_label', 'response_label', 'timestamp']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in raw data: {missing}")
    
    return df

def validate_judgments(df):
    """
    Validate the raw judgments dataframe.

    Args:
        df (pd.DataFrame): Raw judgments dataframe.

    Returns:
        pd.DataFrame: Validated dataframe.
    """
    logger.info("Validating judgments...")
    
    # Check for unique participant IDs
    n_participants = df['participant_id'].nunique()
    if n_participants < 5:
        logger.warning(f"Less than 5 unique participants found ({n_participants}). This may be a test or incomplete dataset.")
    
    # Check for non-null values in critical columns
    if df[['true_label', 'response_label']].isnull().any().any():
        logger.warning("Found null values in label columns. Dropping rows with nulls.")
        df = df.dropna(subset=['true_label', 'response_label'])
    
    return df

def compute_accuracy(df):
    """
    Compute accuracy for each row (correct/incorrect).

    Args:
        df (pd.DataFrame): Judgments dataframe.

    Returns:
        pd.DataFrame: DataFrame with 'accuracy' column (1.0 for correct, 0.0 for incorrect).
    """
    df = df.copy()
    df['accuracy'] = (df['true_label'] == df['response_label']).astype(float)
    return df

def aggregate_judgments(df, manifest_path=None):
    """
    Aggregate judgments by stimulus_id, emotion, and flanker_count.

    Args:
        df (pd.DataFrame): Judgments dataframe with accuracy computed.
        manifest_path (str, optional): Path to stimuli manifest to enrich metadata.

    Returns:
        pd.DataFrame: Aggregated dataframe.
    """
    logger.info("Aggregating judgments...")
    
    # Basic aggregation
    agg_df = df.groupby('stimulus_id').agg({
        'accuracy': 'mean',
        'participant_id': 'count'
    }).reset_index()
    agg_df.columns = ['stimulus_id', 'accuracy', 'n_trials']
    
    if manifest_path and Path(manifest_path).exists():
        logger.info(f"Enriching with manifest metadata from {manifest_path}")
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        
        # Convert manifest to DataFrame for merging
        manifest_df = pd.DataFrame(manifest)
        
        # Merge on stimulus_id
        if 'stimulus_id' in manifest_df.columns:
            agg_df = agg_df.merge(manifest_df[['stimulus_id', 'emotion_label', 'flanker_count']], on='stimulus_id', how='left')
        else:
            # Try to extract from filename if column name differs
            if 'file_path' in manifest_df.columns:
                # Simple extraction logic if needed
                pass
    
    return agg_df

def main(args):
    """
    Main entry point for data loading and aggregation.
    """
    ensure_directories()
    
    raw_data_path = "data/interim/raw_pilot_responses.csv"
    manifest_path = "data/interim/stimuli_manifest.json"
    output_path = "data/processed/human_judgments_aggregates.csv"
    
    try:
        # Load
        df = load_raw_judgments(raw_data_path)
        
        # Validate
        df = validate_judgments(df)
        
        # Compute Accuracy
        df = compute_accuracy(df)
        
        # Aggregate
        agg_df = aggregate_judgments(df, manifest_path)
        
        # Save
        agg_df.to_csv(output_path, index=False)
        logger.info(f"Aggregated judgments saved to {output_path}")
        
    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        logger.error("Pipeline cannot proceed without human judgment data. Please run the pilot or provide data manually.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error during data loading/aggregation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load and aggregate human judgment data.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--test-mode", action="store_true", help="Load mock data if real data is missing")
    args = parser.parse_args()
    main(args)
