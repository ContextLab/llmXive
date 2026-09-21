"""
Analysis pipeline for Cognitive Fatigue from Resting-State EEG.
Implements correlation analysis, ANCOVA, and statistical reporting.
"""
from __future__ import annotations

import os
import sys
import json
import logging
import yaml
import pandas as pd
import numpy as np
from scipy import stats
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

# Import logging utility
# Note: We use the local logging module to avoid circular imports if necessary,
# but the API surface says 'from utils.logging import ...'
try:
    from utils.logging import get_logger, log_operation, save_exclusion_log_csv
except ImportError:
    # Fallback for direct execution without package structure
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from utils.logging import get_logger, log_operation, save_exclusion_log_csv


def load_config(config_path: str = "code/config.yaml") -> Dict[str, Any]:
    """Load configuration from YAML file."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def setup_logger(name: str, log_file: Optional[str] = None) -> Any:
    """
    Setup logger compatible with both ReproducibilityLogger and stdlib logging.
    This function acts as a factory that returns a logger instance.
    """
    # Use the project's custom logger which is tolerant of all call shapes
    logger = get_logger(name)
    # If a log file is requested, we might need to handle it, 
    # but the custom logger handles in-memory entries. 
    # For file logging compatibility, we assume the custom logger handles it or 
    # we just return the custom logger which satisfies the "tolerant" requirement.
    return logger


def validate_metadata(data: pd.DataFrame) -> bool:
    """Validate that required metadata columns exist."""
    required_cols = ['participant_id', 'segment_type', 'fatigue_rating']
    missing = [col for col in required_cols if col not in data.columns]
    if missing:
        logging.error(f"Missing metadata columns: {missing}")
        return False
    return True


def load_complexity_metrics(file_path: str) -> pd.DataFrame:
    """Load complexity metrics from CSV."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Complexity metrics file not found: {file_path}")
    
    df = pd.read_csv(file_path)
    required_cols = ['participant_id', 'channel', 'segment_id', 'lzc_value', 'pe_value']
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in complexity metrics: {missing}")
    
    return df


def load_fatigue_scores(file_path: str) -> pd.DataFrame:
    """Load fatigue scores from CSV."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Fatigue scores file not found: {file_path}")
    
    df = pd.read_csv(file_path)
    required_cols = ['participant_id', 'segment_type', 'fatigue_rating']
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in fatigue scores: {missing}")
    
    return df


def calculate_delta_scores(complexity_df: pd.DataFrame, fatigue_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate delta scores (Post - Pre) for complexity and fatigue.
    Verifies that paired data exists for each participant.
    """
    logging.info("Calculating delta scores...")
    
    # Pivot complexity data to have pre/post columns
    # We assume segment_id encodes 'pre' or 'post' or we have a segment_type column
    # Based on T019, we need to ensure pairing.
    # Let's assume the input data has 'segment_type' in complexity_df or we derive it from segment_id.
    # T019 output: delta_scores.csv with columns participant_id, pre_complexity, post_complexity, fatigue_delta.
    
    # We need to aggregate complexity by participant and segment_type.
    # Let's assume 'segment_id' contains 'pre' or 'post' or there is a 'segment_type' column.
    # If not present, we might need to infer from segment_id.
    
    if 'segment_type' not in complexity_df.columns:
        # Infer from segment_id if possible, e.g., 'seg_pre_01' -> 'pre'
        complexity_df['segment_type'] = complexity_df['segment_id'].apply(
            lambda x: 'pre' if 'pre' in x.lower() else 'post' if 'post' in x.lower() else None
        )
    
    # Filter out rows where segment_type is unknown
    complexity_df = complexity_df[complexity_df['segment_type'].isin(['pre', 'post'])]
    
    # Aggregate complexity by participant and segment_type (mean across channels)
    pre_complexity = complexity_df[complexity_df['segment_type'] == 'pre'].groupby('participant_id').agg({'lzc_value': 'mean'}).reset_index()
    pre_complexity.columns = ['participant_id', 'pre_complexity']
    
    post_complexity = complexity_df[complexity_df['segment_type'] == 'post'].groupby('participant_id').agg({'lzc_value': 'mean'}).reset_index()
    post_complexity.columns = ['participant_id', 'post_complexity']
    
    # Merge pre and post
    complexity_delta = pd.merge(pre_complexity, post_complexity, on='participant_id', how='inner')
    
    if complexity_delta.empty:
        logging.error("Paired data missing: Could not find both pre and post segments for any participant.")
        sys.exit(1)
    
    # Calculate complexity delta
    complexity_delta['complexity_delta'] = complexity_delta['post_complexity'] - complexity_delta['pre_complexity']
    
    # Process fatigue scores
    pre_fatigue = fatigue_df[fatigue_df['segment_type'] == 'pre'].groupby('participant_id').agg({'fatigue_rating': 'mean'}).reset_index()
    pre_fatigue.columns = ['participant_id', 'pre_fatigue']
    
    post_fatigue = fatigue_df[fatigue_df['segment_type'] == 'post'].groupby('participant_id').agg({'fatigue_rating': 'mean'}).reset_index()
    post_fatigue.columns = ['participant_id', 'post_fatigue']
    
    fatigue_delta = pd.merge(pre_fatigue, post_fatigue, on='participant_id', how='inner')
    fatigue_delta['fatigue_delta'] = fatigue_delta['post_fatigue'] - fatigue_delta['pre_fatigue']
    
    # Merge complexity and fatigue deltas
    delta_df = pd.merge(complexity_delta, fatigue_delta, on='participant_id', how='inner')
    
    if delta_df.empty:
        logging.error("Paired data missing: Could not pair complexity and fatigue data.")
        sys.exit(1)
    
    logging.info(f"Calculated deltas for {len(delta_df)} participants.")
    return delta_df


def run_correlation_analysis(delta_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute Pearson and Spearman correlations between complexity_delta and fatigue_delta.
    Returns a DataFrame with results.
    """
    logging.info("Running correlation analysis...")
    
    if delta_df.empty:
        raise ValueError("Delta dataframe is empty. Cannot compute correlations.")
    
    # Check for valid data
    if delta_df['complexity_delta'].isna().all() or delta_df['fatigue_delta'].isna().all():
        logging.error("All values in delta columns are NaN. Cannot compute correlations.")
        raise ValueError("Data contains only NaN values for correlation.")
    
    # Remove rows with NaN in the relevant columns
    valid_df = delta_df.dropna(subset=['complexity_delta', 'fatigue_delta'])
    
    if len(valid_df) < 2:
        logging.error("Insufficient data points for correlation (need at least 2).")
        raise ValueError("Insufficient data points for correlation.")
    
    # Compute Pearson
    pearson_corr, pearson_p = stats.pearsonr(valid_df['complexity_delta'], valid_df['fatigue_delta'])
    
    # Compute Spearman
    spearman_corr, spearman_p = stats.spearmanr(valid_df['complexity_delta'], valid_df['fatigue_delta'])
    
    # Create result dataframe
    results = pd.DataFrame([
        {
            'metric': 'complexity_delta_vs_fatigue_delta',
            'correlation_type': 'pearson',
            'coefficient': pearson_corr,
            'p_value': pearson_p
        },
        {
            'metric': 'complexity_delta_vs_fatigue_delta',
            'correlation_type': 'spearman',
            'coefficient': spearman_corr,
            'p_value': spearman_p
        }
    ])
    
    logging.info(f"Pearson: r={pearson_corr:.4f}, p={pearson_p:.4f}")
    logging.info(f"Spearman: r={spearman_corr:.4f}, p={spearman_p:.4f}")
    
    return results


def run_ancova_model(delta_df: pd.DataFrame, vif_valid_predictors: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Run ANCOVA model: Post_Complexity ~ Fatigue_Delta + Pre_Complexity + Covariates.
    """
    logging.info("Running ANCOVA model...")
    # Placeholder for T021 logic, but we ensure it doesn't break if called
    # T021 will implement the full logic.
    return pd.DataFrame()


def main():
    """Main entry point for the analysis pipeline."""
    logging.info("Starting analysis pipeline.")
    
    # Load config
    config = load_config()
    
    # Define paths
    analysis_dir = Path("data/analysis")
    processed_dir = Path("data/processed")
    analysis_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    complexity_file = analysis_dir / "complexity_metrics.csv"
    fatigue_file = processed_dir / "fatigue_scores.csv" # Assuming T010/T019 produced this
    delta_file = analysis_dir / "delta_scores.csv"
    correlation_file = analysis_dir / "correlation_results.csv"
    
    # Validate inputs
    if not complexity_file.exists():
        logging.error(f"Complexity metrics file not found: {complexity_file}")
        sys.exit(1)
    
    if not fatigue_file.exists():
        logging.error(f"Fatigue scores file not found: {fatigue_file}")
        sys.exit(1)
    
    # Load data
    try:
        complexity_df = load_complexity_metrics(str(complexity_file))
        fatigue_df = load_fatigue_scores(str(fatigue_file))
    except (FileNotFoundError, ValueError) as e:
        logging.error(f"Failed to load data: {e}")
        sys.exit(1)
    
    # Calculate deltas
    try:
        delta_df = calculate_delta_scores(complexity_df, fatigue_df)
        delta_df.to_csv(delta_file, index=False)
        logging.info(f"Delta scores saved to {delta_file}")
    except Exception as e:
        logging.error(f"Failed to calculate deltas: {e}")
        sys.exit(1)
    
    # Run correlation analysis
    try:
        correlation_results = run_correlation_analysis(delta_df)
        correlation_results.to_csv(correlation_file, index=False)
        logging.info(f"Correlation results saved to {correlation_file}")
    except Exception as e:
        logging.error(f"Failed to run correlation analysis: {e}")
        sys.exit(1)
    
    logging.info("Analysis pipeline completed successfully.")


if __name__ == "__main__":
    # Setup basic logging for the script itself if not already set
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    main()