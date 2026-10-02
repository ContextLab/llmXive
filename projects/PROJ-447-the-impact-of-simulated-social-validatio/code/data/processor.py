"""
Data processing module for deriving 'Perceived Social Validation' (PSV).

This module implements the measurement model formula defined in constants.py:
PSV = 0.6 * normalized_likes + 0.4 * normalized_sentiment
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional

from utils.constants import get_psv_weights
from utils.logger import get_logger, log_pipeline_step

logger = get_logger(__name__)


def normalize_column(series: pd.Series, method: str = "minmax") -> pd.Series:
    """
    Normalize a pandas Series to [0, 1] range.

    Args:
        series: Input pandas Series.
        method: Normalization method (currently only 'minmax' supported).

    Returns:
        Normalized Series.
    """
    if method != "minmax":
        raise ValueError(f"Unsupported normalization method: {method}")

    min_val = series.min()
    max_val = series.max()

    if max_val == min_val:
        logger.warning(f"Column has constant value. Returning zeros.")
        return pd.Series(np.zeros(len(series)), index=series.index)

    return (series - min_val) / (max_val - min_val)


def calculate_psv(
    likes: pd.Series,
    sentiment: pd.Series,
    weights: Optional[Dict[str, float]] = None
) -> pd.Series:
    """
    Calculate Perceived Social Validation (PSV) score.

    Formula: 0.6 * normalized_likes + 0.4 * normalized_sentiment

    Args:
        likes: Series of raw like counts.
        sentiment: Series of sentiment scores.
        weights: Optional dictionary of weights. Defaults to config.

    Returns:
        Series of PSV scores.
    """
    if weights is None:
        weights = get_psv_weights()

    w_likes = weights.get('likes', 0.6)
    w_sentiment = weights.get('sentiment', 0.4)

    logger.info(f"Calculating PSV with weights: likes={w_likes}, sentiment={w_sentiment}")

    norm_likes = normalize_column(likes)
    norm_sentiment = normalize_column(sentiment)

    psv = (w_likes * norm_likes) + (w_sentiment * norm_sentiment)

    return psv


def add_psv_column(
    df: pd.DataFrame,
    likes_col: str = "likes",
    sentiment_col: str = "sentiment_score",
    output_col: str = "psv_score"
) -> pd.DataFrame:
    """
    Add PSV column to the DataFrame.

    Args:
        df: Input DataFrame.
        likes_col: Column name for likes.
        sentiment_col: Column name for sentiment scores.
        output_col: Column name for the resulting PSV score.

    Returns:
        DataFrame with added PSV column.
    """
    if likes_col not in df.columns or sentiment_col not in df.columns:
        raise ValueError(f"Required columns '{likes_col}' or '{sentiment_col}' not found.")

    log_pipeline_step(f"Calculating {output_col} from {likes_col} and {sentiment_col}")

    df[output_col] = calculate_psv(df[likes_col], df[sentiment_col])

    logger.info(f"Added {output_col} column. Range: [{df[output_col].min():.4f}, {df[output_col].max():.4f}]")
    return df


def main() -> None:
    """
    Main entry point for data processing.
    Loads data, calculates PSV, and saves results.
    """
    from pathlib import Path
    base_dir = Path(__file__).resolve().parents[2]
    input_path = base_dir / "data" / "processed" / "pipeline_data.csv"
    output_path = base_dir / "data" / "processed" / "pipeline_data_processed.csv"

    logger.info("Executing main() for data processor")

    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        return

    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)

    df = add_psv_column(df)

    df.to_csv(output_path, index=False)
    logger.info(f"Processed data saved to {output_path}")


if __name__ == "__main__":
    import os
    main()
