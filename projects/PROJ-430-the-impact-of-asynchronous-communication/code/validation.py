"""
Multi-modal validation logic to align VADER sentiment scores with manual ground truth data.

This module implements the preparation and execution of validation logic (FR-009),
specifically aligning the computed cohesion_proxy_score (derived from VADER) with
the manually annotated cohesion scores from external human annotators.

It performs:
1. Loading of derived sentiment data (from sentiment.py pipeline).
2. Loading of manual ground truth (from T022b).
3. Alignment/Joining of datasets on project_id.
4. Calculation of preliminary alignment statistics (correlation, MAE, RMSE).
5. Logging of validation readiness and initial metrics.

Note: The actual Spearman correlation calculation and hypothesis testing (T023a)
are performed in `code/analysis.py`. This module prepares the aligned dataset
and performs the initial sanity checks required before that step.
"""

import logging
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

import pandas as pd
import numpy as np

from config import get_config, ensure_directories_exist
from utils.logger import get_logger
from ingest_ground_truth import load_ground_truth

# Initialize logger
logger = get_logger(__name__)

# Constants
SENTIMENT_DATA_PATH = "data/derived/project_cohesion_scores.csv"
GROUND_TRUTH_PATH = "data/validation/manual_ground_truth.csv"
ALIGNED_OUTPUT_PATH = "data/validation/aligned_validation_dataset.csv"
VALIDATION_STATS_PATH = "data/validation/validation_statistics.json"

def load_sentiment_derived_data(config: Dict[str, Any]) -> Optional[pd.DataFrame]:
    """
    Load the project-level cohesion proxy scores derived from sentiment analysis.
    
    Expects the output from the sentiment pipeline (T020) to be at:
    `data/derived/project_cohesion_scores.csv`
    
    Args:
        config: Project configuration dictionary.
        
    Returns:
        DataFrame with project_id and cohesion_proxy_score, or None if file missing.
    """
    data_dir = Path(config['paths']['data_dir'])
    file_path = data_dir / SENTIMENT_DATA_PATH
    
    if not file_path.exists():
        logger.error(f"Sentiment derived data not found at {file_path}. "
                     "Ensure T020 (sentiment aggregation) has been run.")
        return None
        
    try:
        df = pd.read_csv(file_path)
        required_cols = ['project_id', 'cohesion_proxy_score']
        if not all(col in df.columns for col in required_cols):
            missing = set(required_cols) - set(df.columns)
            logger.error(f"Sentiment data missing required columns: {missing}")
            return None
            
        logger.info(f"Loaded sentiment data for {len(df)} projects from {file_path}")
        return df[['project_id', 'cohesion_proxy_score']]
    except Exception as e:
        logger.error(f"Failed to load sentiment data: {e}")
        return None

def load_manual_ground_truth(config: Dict[str, Any]) -> Optional[pd.DataFrame]:
    """
    Load the manual ground truth data ingested by T022b.
    
    Args:
        config: Project configuration dictionary.
        
    Returns:
        DataFrame with project_id and manual_cohesion_score, or None if missing.
    """
    data_dir = Path(config['paths']['data_dir'])
    file_path = data_dir / GROUND_TRUTH_PATH
    
    if not file_path.exists():
        logger.error(f"Manual ground truth not found at {file_path}. "
                     "Ensure T022b (ground truth ingestion) has been run.")
        return None
        
    try:
        # T022b produces a file with project_id, comment_id, manual_cohesion_score
        # For project-level validation, we need to aggregate this to project level
        # or ensure we are comparing at the appropriate granularity.
        # The plan implies project-level comparison (US2 Goal: "Apply VADER... to derive cohesion_proxy_score").
        # If the ground truth is per-comment, we aggregate to project level (mean) for alignment.
        df = pd.read_csv(file_path)
        
        required_cols = ['project_id', 'manual_cohesion_score']
        if not all(col in df.columns for col in required_cols):
            missing = set(required_cols) - set(df.columns)
            logger.error(f"Ground truth missing required columns: {missing}")
            return None
            
        # Aggregate to project level if multiple comments exist per project
        # This aligns with the project-level cohesion_proxy_score from T020
        project_scores = df.groupby('project_id')['manual_cohesion_score'].mean().reset_index()
        
        logger.info(f"Loaded and aggregated ground truth for {len(project_scores)} projects from {file_path}")
        return project_scores
    except Exception as e:
        logger.error(f"Failed to load ground truth: {e}")
        return None

def align_datasets(sentiment_df: pd.DataFrame, ground_truth_df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, int]]:
    """
    Align sentiment scores with manual ground truth on project_id.
    
    Args:
        sentiment_df: DataFrame with project_id and cohesion_proxy_score.
        ground_truth_df: DataFrame with project_id and manual_cohesion_score.
        
    Returns:
        Tuple of (aligned DataFrame, stats dict with counts).
    """
    if sentiment_df is None or ground_truth_df is None:
        logger.error("Cannot align datasets: one or both inputs are None.")
        return pd.DataFrame(), {'matched': 0, 'sentiment_only': 0, 'ground_truth_only': 0}
    
    # Inner join to ensure we only compare projects with both scores
    aligned = pd.merge(
        sentiment_df, 
        ground_truth_df, 
        on='project_id', 
        how='inner'
    )
    
    stats = {
        'matched': len(aligned),
        'sentiment_only': len(sentiment_df) - len(aligned),
        'ground_truth_only': len(ground_truth_df) - len(aligned)
    }
    
    if stats['matched'] == 0:
        logger.warning("No projects found with both VADER and manual scores. "
                       "Validation cannot proceed without overlapping data.")
    else:
        logger.info(f"Aligned {stats['matched']} projects for validation.")
        
    return aligned, stats

def calculate_alignment_metrics(aligned_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate preliminary alignment metrics (MAE, RMSE, Pearson correlation).
    
    These are descriptive statistics to prepare for the formal hypothesis test (T023a).
    
    Args:
        aligned_df: DataFrame with 'cohesion_proxy_score' and 'manual_cohesion_score'.
        
    Returns:
        Dictionary of metrics.
    """
    if aligned_df.empty:
        return {}
        
    vader = aligned_df['cohesion_proxy_score']
    manual = aligned_df['manual_cohesion_score']
    
    # Drop NaNs if any
    valid_pairs = pd.notna(vader) & pd.notna(manual)
    vader = vader[valid_pairs]
    manual = manual[valid_pairs]
    
    if len(vader) < 2:
        logger.warning("Insufficient data points for correlation calculation.")
        return {'count': len(vader)}
    
    mae = np.mean(np.abs(vader - manual))
    rmse = np.sqrt(np.mean((vader - manual) ** 2))
    
    # Pearson correlation (linear relationship)
    # Note: T023a will perform Spearman (rank) correlation as per SC-005
    pearson_r = np.corrcoef(vader, manual)[0, 1] if len(vader) > 1 else np.nan
    
    return {
        'count': len(vader),
        'mae': float(mae),
        'rmse': float(rmse),
        'pearson_r': float(pearson_r) if not np.isnan(pearson_r) else None
    }

def run_validation_pipeline(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Execute the multi-modal validation preparation pipeline.
    
    1. Load sentiment derived data.
    2. Load manual ground truth.
    3. Align datasets.
    4. Calculate preliminary metrics.
    5. Save aligned dataset and stats.
    
    Args:
        config: Optional config dict. If None, loads from get_config().
        
    Returns:
        Dictionary containing pipeline status and metrics.
    """
    if config is None:
        config = get_config()
        
    ensure_directories_exist(config)
    
    logger.info("Starting multi-modal validation preparation (T023)...")
    
    # Load data
    sentiment_df = load_sentiment_derived_data(config)
    ground_truth_df = load_manual_ground_truth(config)
    
    if sentiment_df is None or ground_truth_df is None:
        logger.error("Validation pipeline aborted due to missing input data.")
        return {
            'status': 'failed',
            'reason': 'Missing input data (sentiment or ground truth)',
            'matched_projects': 0
        }
    
    # Align
    aligned_df, alignment_stats = align_datasets(sentiment_df, ground_truth_df)
    
    if aligned_df.empty:
        logger.error("Validation pipeline aborted: No overlapping projects found.")
        return {
            'status': 'failed',
            'reason': 'No overlapping projects between sentiment and ground truth',
            'matched_projects': 0
        }
    
    # Calculate metrics
    metrics = calculate_alignment_metrics(aligned_df)
    
    # Save aligned dataset for downstream analysis (T023a, T025)
    output_path = Path(config['paths']['data_dir']) / ALIGNED_OUTPUT_PATH
    aligned_df.to_csv(output_path, index=False)
    logger.info(f"Saved aligned validation dataset to {output_path}")
    
    # Prepare final stats
    result = {
        'status': 'success',
        'alignment_stats': alignment_stats,
        'metrics': metrics,
        'output_path': str(output_path),
        'next_step': 'T023a (Spearman correlation and threshold check)'
    }
    
    logger.info(f"Validation preparation complete. Matched projects: {alignment_stats['matched']}")
    logger.info(f"MAE: {metrics.get('mae', 'N/A'):.4f}, RMSE: {metrics.get('rmse', 'N/A'):.4f}")
    
    return result

def main():
    """Entry point for running the validation pipeline."""
    config = get_config()
    result = run_validation_pipeline(config)
    
    if result['status'] == 'success':
        print(f"Validation preparation successful.")
        print(f"Aligned {result['alignment_stats']['matched']} projects.")
        print(f"Metrics: {result['metrics']}")
    else:
        print(f"Validation preparation failed: {result['reason']}")
        sys.exit(1)

if __name__ == '__main__':
    main()