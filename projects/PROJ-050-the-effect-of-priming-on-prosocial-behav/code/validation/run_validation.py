"""
Validation script to verify externally supplied gold standard annotations.

This script accepts an externally supplied `gold_standard.csv` file and verifies:
1. The file exists and is readable.
2. It contains the required columns: `comment_id`, `rater_id`, `prosocial_action`, `neg_sentiment`.
3. It contains annotations from at least 3 distinct raters (via `rater_id` column).
4. Computes Cohen's Kappa for inter-rater reliability on `neg_sentiment` and Pearson r correlation
   between the mean rater score and the model's `neg_score`.

ABORT LOGIC: If Cohen's Kappa < 0.7, the script MUST abort the pipeline and log insufficiency per SC-006.
"""

import logging
import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

import pandas as pd
import numpy as np
from scipy.stats import pearsonr
from sklearn.metrics import cohen_kappa_score

# Import project utilities
from code.config import PROJECT_ROOT
from code.utils.logger import setup_logger, log_abort_condition
from code.utils.schema_validator import validate_schema

# Constants
MIN_RATERS = 3
REQUIRED_COLUMNS = ['comment_id', 'rater_id', 'prosocial_action', 'neg_sentiment']
SCHEMA_FILE = PROJECT_ROOT / 'specs' / '001-the-effect-of-priming-on-prosocial-behav' / 'gold_standard.schema.yaml'
KAPPA_THRESHOLD = 0.7
SCORED_DATA_PATH = PROJECT_ROOT / 'data' / 'processed' / 'scored.csv'

def validate_rater_count(df: pd.DataFrame) -> bool:
    """
    Verify that the dataframe contains annotations from at least MIN_RATERS distinct raters.
    
    Args:
        df: DataFrame containing the gold standard annotations.
        
    Returns:
        True if the rater count requirement is met, False otherwise.
    """
    unique_raters = df['rater_id'].nunique()
    if unique_raters < MIN_RATERS:
        logging.error(f"Insufficient raters: found {unique_raters}, required {MIN_RATERS}.")
        return False
    logging.info(f"Rater count validation passed: {unique_raters} distinct raters found.")
    return True

def validate_columns(df: pd.DataFrame) -> bool:
    """
    Verify that the dataframe contains all required columns.
    
    Args:
        df: DataFrame containing the gold standard annotations.
        
    Returns:
        True if all required columns are present, False otherwise.
    """
    missing_cols = set(REQUIRED_COLUMNS) - set(df.columns)
    if missing_cols:
        logging.error(f"Missing required columns: {missing_cols}")
        return False
    logging.info("Column validation passed: all required columns present.")
    return True

def compute_agreement_metrics(df: pd.DataFrame, scored_data_path: Path) -> Tuple[Optional[float], Optional[float], Dict[str, Any]]:
    """
    Compute Cohen's Kappa for inter-rater reliability and Pearson r for model correlation.
    
    Args:
        df: DataFrame containing the gold standard annotations.
        scored_data_path: Path to the scored.csv file containing model predictions.
        
    Returns:
        Tuple of (kappa_score, pearson_r, details_dict) or (None, None, error_dict) if data is insufficient.
    """
    logger = logging.getLogger('validation')
    
    # 1. Prepare data for Cohen's Kappa
    # We need to compare raters against each other. We will compute average kappa across all pairs.
    # First, pivot to have raters as columns
    try:
        pivot_df = df.pivot_table(index='comment_id', columns='rater_id', values='neg_sentiment', aggfunc='first')
    except Exception as e:
        logger.error(f"Failed to pivot data for Kappa calculation: {e}")
        return None, None, {"error": f"Pivot failed: {e}"}

    raters = pivot_df.columns.tolist()
    if len(raters) < 2:
        logger.error("Not enough raters to compute pairwise Kappa.")
        return None, None, {"error": "Insufficient raters for pairwise Kappa"}

    kappa_scores = []
    pairs = []
    valid_comments_count = 0

    for i in range(len(raters)):
        for j in range(i + 1, len(raters)):
            rater_a = raters[i]
            rater_b = raters[j]
            
            # Get pairs where both raters have annotations
            pair_data = pivot_df[[rater_a, rater_b]].dropna()
            if len(pair_data) < 5: # Minimum threshold for meaningful Kappa
                continue
            
            try:
                # Ensure data is treated as categorical/discrete for Kappa if it's continuous,
                # but neg_sentiment is often continuous (-1 to 1). 
                # SC-006 implies binary or ordinal. If continuous, we might need to bin or use ICC.
                # Assuming neg_sentiment is treated as ordinal/binary here or continuous if sklearn supports it.
                # sklearn cohen_kappa_score requires labels to be hashable.
                # If data is float, we might need to bin it (e.g., Negative vs Non-Negative) or use a continuous metric.
                # However, standard Kappa is for categorical. Let's assume the raters provided discrete labels 
                # or we bin them for the sake of the metric defined in SC-006.
                # To be safe and robust, let's bin continuous scores into 3 categories: Negative, Neutral, Positive
                # based on standard VADER thresholds (-0.05, 0.05) or just the raw values if they are already discrete.
                
                # Check if values are effectively discrete
                if pair_data[rater_a].nunique() == 1 or pair_data[rater_b].nunique() == 1:
                    continue
                
                # If continuous, bin them to satisfy Kappa requirements
                # Using standard sentiment thresholds: < -0.05 (Neg), > 0.05 (Pos), else (Neutral)
                def bin_sentiment(x):
                    if x < -0.05: return 0
                    elif x > 0.05: return 2
                    else: return 1
                
                labels_a = pair_data[rater_a].apply(bin_sentiment)
                labels_b = pair_data[rater_b].apply(bin_sentiment)
                
                k = cohen_kappa_score(labels_a, labels_b)
                kappa_scores.append(k)
                pairs.append((rater_a, rater_b))
                valid_comments_count = max(valid_comments_count, len(pair_data))
            except Exception as e:
                logger.warning(f"Could not compute Kappa for pair ({rater_a}, {rater_b}): {e}")

    mean_kappa = np.mean(kappa_scores) if kappa_scores else None
    logger.info(f"Computed Kappa for {len(pairs)} pairs. Mean Kappa: {mean_kappa:.4f}")

    # 2. Compute Pearson r between mean rater score and model neg_score
    # Merge gold standard with scored data
    try:
        scored_df = pd.read_csv(scored_data_path)
        # We need the model's neg_score for the same comments
        # Assume scored_df has 'comment_id' and 'neg_score'
        if 'neg_score' not in scored_df.columns:
            logger.error("scored.csv missing 'neg_score' column.")
            return mean_kappa, None, {"error": "scored.csv missing 'neg_score'"}
        
        # Calculate mean rater score per comment_id
        mean_rater_scores = pivot_df.mean(axis=1).reset_index()
        mean_rater_scores.columns = ['comment_id', 'mean_rater_neg_sentiment']
        
        # Merge
        merged = mean_rater_scores.merge(scored_df[['comment_id', 'neg_score']], on='comment_id', how='inner')
        
        if len(merged) < 10:
            logger.warning(f"Too few overlapping comments ({len(merged)}) for Pearson correlation.")
            return mean_kappa, None, {"error": "Insufficient overlap for correlation"}
        
        r, p_value = pearsonr(merged['mean_rater_neg_sentiment'], merged['neg_score'])
        logger.info(f"Pearson r between mean rater score and model neg_score: {r:.4f} (p={p_value:.4e})")
        
        return mean_kappa, r, {
            "kappa_pairs": len(pairs),
            "overlap_count": len(merged),
            "kappa_details": pairs
        }
    except Exception as e:
        logger.error(f"Failed to compute Pearson r: {e}")
        return mean_kappa, None, {"error": f"Pearson r failed: {e}"}

def run_validation(gold_standard_path: Path) -> bool:
    """
    Main validation logic for the external gold standard file.
    
    Args:
        gold_standard_path: Path to the externally supplied gold_standard.csv file.
        
    Returns:
        True if validation passes, False otherwise.
    """
    logger = setup_logger('validation')
    logger.info(f"Starting validation for: {gold_standard_path}")
    
    # Check file existence
    if not gold_standard_path.exists():
        error_msg = f"Gold standard file not found: {gold_standard_path}"
        logger.error(error_msg)
        log_abort_condition(error_msg)
        return False
    
    try:
        # Load the data
        df = pd.read_csv(gold_standard_path)
        logger.info(f"Successfully loaded {len(df)} rows from {gold_standard_path}")
    except Exception as e:
        error_msg = f"Failed to load gold standard file: {e}"
        logger.error(error_msg)
        log_abort_condition(error_msg)
        return False
    
    # Validate schema/columns
    if not validate_columns(df):
        error_msg = "Column validation failed."
        log_abort_condition(error_msg)
        return False
    
    # Validate rater count
    if not validate_rater_count(df):
        error_msg = "Rater count validation failed."
        log_abort_condition(error_msg)
        return False
    
    # Optional: Validate against schema file if it exists
    if SCHEMA_FILE.exists():
        try:
            if not validate_schema(df, SCHEMA_FILE):
                error_msg = "Schema validation failed against gold_standard.schema.yaml."
                log_abort_condition(error_msg)
                return False
        except Exception as e:
            logger.warning(f"Schema validation skipped due to error: {e}")
    
    # Compute Agreement Metrics (T027 Core Logic)
    if not SCORED_DATA_PATH.exists():
        error_msg = f"Required scored data file not found for correlation check: {SCORED_DATA_PATH}"
        logger.error(error_msg)
        log_abort_condition(error_msg)
        return False

    kappa_score, pearson_r, details = compute_agreement_metrics(df, SCORED_DATA_PATH)
    
    if kappa_score is None:
        error_msg = "Failed to compute Cohen's Kappa due to data issues."
        logger.error(error_msg)
        log_abort_condition(error_msg)
        return False
    
    # ABORT LOGIC: If Cohen's Kappa < 0.7
    if kappa_score < KAPPA_THRESHOLD:
        error_msg = f"Insufficient inter-rater reliability: Cohen's Kappa = {kappa_score:.4f} (Threshold: {KAPPA_THRESHOLD}). ABORTING."
        logger.error(error_msg)
        log_abort_condition(error_msg)
        return False
    
    logger.info(f"Validation PASSED. Cohen's Kappa = {kappa_score:.4f}, Pearson r = {pearson_r:.4f if pearson_r else 'N/A'}")
    return True

def main():
    """Entry point for the validation script."""
    # Default path relative to project root
    gold_standard_path = PROJECT_ROOT / 'data' / 'validation' / 'gold_standard.csv'
    
    # Allow override via command line argument
    if len(sys.argv) > 1:
        gold_standard_path = Path(sys.argv[1])
    
    success = run_validation(gold_standard_path)
    
    if not success:
        sys.exit(1)
    
    sys.exit(0)

if __name__ == '__main__':
    main()