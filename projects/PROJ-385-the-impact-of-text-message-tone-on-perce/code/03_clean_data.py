"""
Data Cleaning Module: Straight-lining detection and missing data handling.

This module implements the cleaning pipeline for the text message tone study.
It performs:
1. Straight-lining detection (identifying participants with zero variance in ratings).
2. Missing data handling via:
   - Listwise deletion (default).
   - MICE (Multiple Imputation by Chained Equations) via sklearn iteratively imputing.
3. Logging of all exclusions and imputation actions.
"""

import csv
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Set, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.experimental import enable_iterative_imputer  # noqa: F401
from sklearn.impute import IterativeImputer

# Local imports
from config import get_processed_data_dir, get_raw_data_dir, get_data_dir
from logging_config import setup_logging, get_logger, log_exclusion

# Constants
STRAIGHT_LINING_THRESHOLD = 0.0  # Variance below this is considered straight-lining
MISSING_VALUE_INDICATOR = -999   # Internal marker for missing data before imputation

logger = get_logger(__name__)


def load_stimuli(stimuli_path: Optional[Path] = None) -> pd.DataFrame:
    """Load the stimuli dataframe."""
    if stimuli_path is None:
        stimuli_path = get_raw_data_dir() / "stimuli.csv"
    
    if not stimuli_path.exists():
        logger.error(f"Stimuli file not found: {stimuli_path}")
        raise FileNotFoundError(f"Stimuli file not found: {stimuli_path}")
    
    return pd.read_csv(stimuli_path)


def load_ratings(ratings_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load the ratings dataframe (anonymised).
    Expected columns include: participant_id, stimulus_id, context, 
    emotional_support_rating, and potentially others.
    """
    if ratings_path is None:
        # T051 produces anonymised_ratings.csv in data/processed/
        ratings_path = get_processed_data_dir() / "anonymised_ratings.csv"
    
    if not ratings_path.exists():
        logger.error(f"Ratings file not found: {ratings_path}")
        raise FileNotFoundError(f"Ratings file not found: {ratings_path}")
    
    df = pd.read_csv(ratings_path)
    logger.info(f"Loaded {len(df)} ratings from {ratings_path}")
    return df


def detect_straight_lining(df: pd.DataFrame, rating_column: str = "emotional_support_rating") -> Tuple[pd.DataFrame, List[str]]:
    """
    Detect straight-lining behavior.
    
    A participant is flagged as straight-lining if the variance of their ratings
    across all trials is below the threshold (effectively zero).
    
    Args:
        df: The ratings dataframe.
        rating_column: The column name containing the numeric ratings.
        
    Returns:
        A tuple (cleaned_df, excluded_participant_ids).
        cleaned_df: The dataframe with straight-lining participants removed.
        excluded_participant_ids: List of participant IDs that were excluded.
    """
    if rating_column not in df.columns:
        logger.error(f"Rating column '{rating_column}' not found in dataframe.")
        raise ValueError(f"Rating column '{rating_column}' not found.")

    # Calculate variance per participant
    participant_stats = df.groupby('participant_id')[rating_column].agg(['var', 'count'])
    
    # Identify straight-lining participants (variance == 0 or NaN if only 1 rating)
    # We exclude participants with 0 variance.
    # Note: If a participant has only 1 rating, variance is NaN. 
    # Depending on strictness, we might exclude them too, but typically we need >1 rating.
    # For this task, we strictly flag variance == 0.
    straight_liners = participant_stats[participant_stats['var'] == 0.0].index.tolist()
    
    # Also flag participants with NaN variance (single response) if we want to be strict,
    # but standard straight-lining usually implies multiple identical responses.
    # Let's stick to variance == 0 for "identical responses".
    
    excluded_ids = []
    for pid in straight_liners:
        excluded_ids.append(pid)
        log_exclusion(
            reason="straight_lining",
            participant_id=pid,
            details="Zero variance in emotional_support_rating across trials.",
            logger=logger
        )
    
    if excluded_ids:
        logger.warning(f"Detected {len(excluded_ids)} straight-lining participants.")
        cleaned_df = df[~df['participant_id'].isin(excluded_ids)].copy()
    else:
        logger.info("No straight-lining participants detected.")
        cleaned_df = df.copy()
        
    return cleaned_df, excluded_ids


def handle_missing_data(
    df: pd.DataFrame, 
    rating_column: str = "emotional_support_rating",
    strategy: str = "listwise"
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Handle missing data in the dataset.
    
    Strategies:
    - 'listwise': Drop any row with missing values in the target rating column.
    - 'mice': Use IterativeImputer (MICE) to impute missing values based on other features.
    
    Args:
        df: The dataframe to clean.
        rating_column: The target column for imputation/deletion.
        strategy: 'listwise' or 'mice'.
        
    Returns:
        Tuple of (cleaned_df, stats_dict).
    """
    stats = {
        "initial_rows": len(df),
        "missing_count": df[rating_column].isna().sum(),
        "strategy_used": strategy,
        "rows_removed": 0,
        "rows_imputed": 0
    }

    if stats["missing_count"] == 0:
        logger.info("No missing data found in the target column.")
        return df, stats

    if strategy == "listwise":
        logger.info(f"Applying listwise deletion for missing {rating_column} values.")
        initial_count = len(df)
        df_clean = df.dropna(subset=[rating_column])
        removed_count = initial_count - len(df_clean)
        stats["rows_removed"] = removed_count
        logger.info(f"Listwise deletion removed {removed_count} rows.")
        return df_clean, stats

    elif strategy == "mice":
        if not np.any(df[rating_column].isna()):
            return df, stats
        
        logger.info("Applying MICE (IterativeImputer) for missing data.")
        
        # Prepare data for imputation
        # We need numeric columns to perform imputation. 
        # We'll impute based on available numeric features if any, or just the target if isolated.
        # For simplicity in this context, we assume we might have other numeric features like 'cue_intensity' 
        # or we just impute the rating based on the distribution if no other numeric features exist.
        # However, sklearn's IterativeImputer requires at least 2 features or a specific estimator setup.
        
        # Let's select numeric columns for the imputer context.
        # We include 'cue_intensity' if it exists, otherwise we might need to create a dummy feature 
        # or just use the mean if no other numeric data exists (though MICE is overkill then).
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        # Ensure the target column is in the numeric list for the imputer to handle
        if rating_column not in numeric_cols:
            # Convert to numeric if possible
            df[rating_column] = pd.to_numeric(df[rating_column], errors='coerce')
            numeric_cols.append(rating_column)
        
        if len(numeric_cols) < 2:
            logger.warning("Insufficient numeric features for MICE. Falling back to mean imputation.")
            mean_val = df[rating_column].mean()
            df[rating_column] = df[rating_column].fillna(mean_val)
            stats["rows_imputed"] = df[rating_column].isna().sum() # Should be 0
            return df, stats

        # Prepare the subset for imputation
        impute_data = df[numeric_cols].copy()
        
        # Initialize MICE
        # Using a simple estimator like BayesianRidge is often more stable than RandomForest for small data
        imputer = IterativeImputer(random_state=42, max_iter=10, tol=0.001)
        
        try:
            imputed_values = imputer.fit_transform(impute_data)
            imputed_df = pd.DataFrame(imputed_values, columns=numeric_cols, index=df.index)
            
            # Update the original dataframe
            for col in numeric_cols:
                df[col] = imputed_df[col]
            
            # Verify no missing values remain
            remaining_missing = df[rating_column].isna().sum()
            if remaining_missing > 0:
                logger.error(f"MICE failed to impute all values. Remaining: {remaining_missing}")
                # Fallback to listwise if MICE fails partially? 
                # For now, we raise to fail loudly as per constraints.
                raise RuntimeError("MICE imputation incomplete.")
                
            stats["rows_imputed"] = stats["missing_count"]
            logger.info(f"MICE imputation successful. Imputed {stats['rows_imputed']} values.")
            return df, stats
            
        except Exception as e:
            logger.error(f"MICE imputation failed: {e}")
            raise


def save_cleaning_log(exclusions: List[Dict[str, Any]], log_path: Optional[Path] = None) -> None:
    """Save the cleaning log to a JSON file."""
    if log_path is None:
        log_path = get_processed_data_dir() / "cleaning_log.json"
    
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "exclusions": exclusions
    }
    
    with open(log_path, 'w') as f:
        json.dump(log_entry, f, indent=2)
    
    logger.info(f"Cleaning log saved to {log_path}")


def save_cleaned_ratings(df: pd.DataFrame, output_path: Optional[Path] = None) -> None:
    """Save the cleaned dataframe to CSV."""
    if output_path is None:
        output_path = get_processed_data_dir() / "cleaned_ratings.csv"
    
    df.to_csv(output_path, index=False)
    logger.info(f"Cleaned ratings saved to {output_path} ({len(df)} rows)")


def main():
    """
    Main entry point for the data cleaning pipeline.
    
    Usage:
        python code/03_clean_data.py [--strategy listwise|mice]
    """
    import argparse
    
    # Setup logging
    setup_logging()
    
    parser = argparse.ArgumentParser(description="Clean ratings data (straight-lining & missing data).")
    parser.add_argument(
        "--strategy", 
        type=str, 
        choices=["listwise", "mice"], 
        default="listwise",
        help="Strategy for handling missing data (default: listwise)"
    )
    args = parser.parse_args()
    
    logger.info(f"Starting data cleaning with strategy: {args.strategy}")
    
    try:
        # 1. Load Data
        # We expect anonymised_ratings.csv to exist (from T051)
        ratings_df = load_ratings()
        
        # 2. Detect Straight-lining
        cleaned_df, excluded_pids = detect_straight_lining(ratings_df)
        
        # 3. Handle Missing Data
        final_df, missing_stats = handle_missing_data(
            cleaned_df, 
            strategy=args.strategy
        )
        
        # 4. Save Outputs
        save_cleaned_ratings(final_df)
        
        # Log summary
        logger.info(f"Pipeline complete. Initial: {len(ratings_df)}, Final: {len(final_df)}")
        logger.info(f"Excluded (straight-lining): {len(excluded_pids)}")
        logger.info(f"Missing data stats: {missing_stats}")
        
        # Return success
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Data file missing: {e}")
        return 1
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise


if __name__ == "__main__":
    sys.exit(main())
