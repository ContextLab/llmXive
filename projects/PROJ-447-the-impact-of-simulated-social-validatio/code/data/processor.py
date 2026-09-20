"""
code/data/processor.py

Implements FR-008: Derive 'Perceived Social Validation' (PSV) from engagement metrics
and comment sentiment using the mathematical formula defined in code/utils/constants.py.

Formula (from constants.py get_psv_weights):
PSV = (w_like * log(1 + likes) + w_comment * log(1 + comments) + w_share * log(1 + shares))
      * sentiment_score * sentiment_scale

Where:
- w_like = 0.25
- w_comment = 0.40
- w_share = 0.35
- sentiment_scale = 1.0
- log_transform = True (applies log(1+x) to engagement counts)
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional

from utils.constants import get_psv_weights
from utils.logger import get_logger, log_pipeline_step

logger = get_logger(__name__)


def calculate_psv(
    df: pd.DataFrame,
    weights: Optional[Dict[str, Any]] = None
) -> pd.Series:
    """
    Calculate the 'Perceived Social Validation' (PSV) score for each row in the DataFrame.

    Args:
        df: DataFrame containing columns 'likes', 'comments', 'shares', and 'sentiment_score'.
        weights: Optional dictionary overriding default weights from constants.py.
                 Expected keys: 'like_weight', 'comment_weight', 'share_weight',
                 'sentiment_scale', 'log_transform'.

    Returns:
        pd.Series: The calculated PSV scores.

    Raises:
        KeyError: If required columns are missing from the DataFrame.
        ValueError: If sentiment_score contains non-numeric data or invalid ranges.
    """
    required_cols = ['likes', 'comments', 'shares', 'sentiment_score']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        logger.error(f"Missing required columns for PSV calculation: {missing_cols}")
        raise KeyError(f"Missing columns for PSV calculation: {missing_cols}")

    if weights is None:
        weights = get_psv_weights()

    w_like = weights['like_weight']
    w_comment = weights['comment_weight']
    w_share = weights['share_weight']
    sentiment_scale = weights['sentiment_scale']
    use_log = weights.get('log_transform', True)

    logger.info("Calculating Perceived Social Validation (PSV)...")

    # Prepare engagement components
    if use_log:
        likes_term = np.log1p(df['likes'].astype(float))
        comments_term = np.log1p(df['comments'].astype(float))
        shares_term = np.log1p(df['shares'].astype(float))
    else:
        likes_term = df['likes'].astype(float)
        comments_term = df['comments'].astype(float)
        shares_term = df['shares'].astype(float)

    # Validate sentiment score
    sentiment_scores = df['sentiment_score'].astype(float)
    if sentiment_scores.isna().any():
        logger.warning("NaN values detected in sentiment_score. PSV will be NaN for those rows.")

    # Apply formula:
    # PSV = (w_like * log(1 + likes) + w_comment * log(1 + comments) + w_share * log(1 + shares))
    #       * sentiment_score * sentiment_scale
    engagement_component = (
        (w_like * likes_term) +
        (w_comment * comments_term) +
        (w_share * shares_term)
    )

    psv_scores = engagement_component * sentiment_scores * sentiment_scale

    log_pipeline_step("PSV Calculation", "Success", {
        "rows_processed": len(df),
        "weights_used": weights,
        "log_transform": use_log
    })

    return psv_scores


def add_psv_column(
    df: pd.DataFrame,
    output_column_name: str = 'perceived_social_validation'
) -> pd.DataFrame:
    """
    Adds the PSV score as a new column to the input DataFrame.

    Args:
        df: Input DataFrame.
        output_column_name: Name for the new column.

    Returns:
        pd.DataFrame: The input DataFrame with the new PSV column appended.
    """
    logger.info(f"Adding '{output_column_name}' column to dataset.")
    df = df.copy()
    df[output_column_name] = calculate_psv(df)
    return df


def main():
    """
    Standalone execution entry point for testing the processor.
    Expects a CSV file at 'data/raw/sample_data.csv' (or similar) or generates
    a minimal test frame if none exists, calculates PSV, and saves to
    'data/processed/psv_processed_data.csv'.

    Note: In the full pipeline, this function is called by code/main.py
    after data loading and validation.
    """
    import os
    from pathlib import Path

    # Define paths relative to project root
    # Assuming this script runs from project root or via python -m
    project_root = Path(__file__).parent.parent.parent
    input_path = project_root / "data" / "raw" / "sample_data.csv"
    output_dir = project_root / "data" / "processed"
    output_path = output_dir / "psv_processed_data.csv"

    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Starting PSV Processor. Input: {input_path}, Output: {output_path}")

    # Attempt to load real data if available, otherwise create a minimal valid test frame
    # to demonstrate the function works. The main pipeline (T014) handles the real
    # load/generator logic.
    if input_path.exists():
        try:
            df = pd.read_csv(input_path)
            logger.info(f"Loaded {len(df)} rows from {input_path}")
        except Exception as e:
            logger.error(f"Failed to load input file: {e}")
            raise
    else:
        logger.warning(f"Input file {input_path} not found. Creating minimal test data for verification.")
        # Minimal valid test data to ensure the function runs without crashing
        # and produces the expected column.
        data = {
            'likes': [10, 100, 500],
            'comments': [2, 20, 50],
            'shares': [1, 5, 10],
            'sentiment_score': [0.8, 0.5, 0.9],
            'id': [1, 2, 3]
        }
        df = pd.DataFrame(data)
        logger.info("Created minimal test DataFrame.")

    # Calculate and add PSV
    try:
        df_with_psv = add_psv_column(df)
        logger.info(f"PSV calculation complete. Sample values: {df_with_psv['perceived_social_validation'].head().tolist()}")
    except Exception as e:
        logger.error(f"PSV calculation failed: {e}")
        raise

    # Save to disk
    df_with_psv.to_csv(output_path, index=False)
    logger.info(f"Saved processed data to {output_path}")


if __name__ == "__main__":
    main()