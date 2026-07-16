"""
Edge Case Handler for the Linguistic Cues Research Pipeline.

This module implements FR-007 by detecting:
1. Empty or short texts (< 5 words)
2. Missing ratings in the dataset

Upon detection of missing ratings, the handler logs a structured error and
triggers a pipeline HALT (sys.exit) rather than attempting auto-annotation.
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd

# Configure logging for this module
logger = logging.getLogger(__name__)

# Minimum word count threshold for valid text
MIN_WORD_COUNT = 5


def log_exclusions(
    exclusions: List[Dict[str, Any]],
    log_dir: Path,
    prefix: str = "edge_case_exclusions"
) -> Path:
    """
    Write a structured log of excluded records to a JSON file.

    Args:
        exclusions: List of dictionaries containing exclusion details.
        log_dir: Directory where the log file will be saved.
        prefix: Prefix for the log filename.

    Returns:
        Path to the created log file.
    """
    log_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"{prefix}_{timestamp}.json"

    import json
    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(exclusions, f, indent=2, default=str)

    logger.info(f"Exclusion log written to: {log_file}")
    return log_file


def detect_empty_or_short_texts(
    df: pd.DataFrame,
    text_column: str = "text_content"
) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """
    Detect rows where the text column is empty or contains fewer than MIN_WORD_COUNT words.

    Args:
        df: Input DataFrame containing conversation text.
        text_column: Name of the column containing text data.

    Returns:
        Tuple of (valid_df, exclusions_list)
        - valid_df: DataFrame with short/empty texts removed.
        - exclusions_list: List of dicts with details about excluded rows.
    """
    if text_column not in df.columns:
        logger.warning(f"Column '{text_column}' not found in DataFrame. Skipping text length check.")
        return df, []

    def count_words(text):
        if pd.isna(text) or not isinstance(text, str) or text.strip() == "":
            return 0
        return len(text.split())

    word_counts = df[text_column].apply(count_words)
    mask = word_counts >= MIN_WORD_COUNT
    valid_df = df[mask].copy()
    excluded_df = df[~mask]

    exclusions = []
    for idx, row in excluded_df.iterrows():
        exclusions.append({
            "index": int(idx),
            "reason": "short_or_empty_text",
            "word_count": int(word_counts.loc[idx]),
            "text_preview": str(row[text_column])[:100] if row[text_column] else None
        })

    if exclusions:
        logger.warning(f"Detected {len(exclusions)} rows with text length < {MIN_WORD_COUNT} words.")
    else:
        logger.info("No short or empty texts detected.")

    return valid_df, exclusions


def detect_missing_ratings(
    df: pd.DataFrame,
    ratings_df: Optional[pd.DataFrame] = None,
    text_id_column: str = "conversation_id",
    rating_id_column: str = "conversation_id",
    rating_value_column: str = "authenticity_score"
) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """
    Detect rows in the main DataFrame that are missing corresponding ratings.

    If ratings_df is provided, it checks for existence of the ID in ratings.
    If ratings_df is None, it checks if the rating column exists in the main df.

    Args:
        df: Main DataFrame (e.g., extracted features).
        ratings_df: Optional DataFrame containing human ratings.
        text_id_column: Column name in df for conversation ID.
        rating_id_column: Column name in ratings_df for conversation ID.
        rating_value_column: Column name in ratings_df for the score.

    Returns:
        Tuple of (valid_df, exclusions_list)
        - valid_df: DataFrame with rows that have valid ratings.
        - exclusions_list: List of dicts with details about missing ratings.
    """
    exclusions = []

    # Case 1: Ratings provided in a separate DataFrame
    if ratings_df is not None:
        if rating_id_column not in ratings_df.columns:
            raise ValueError(f"Rating ID column '{rating_id_column}' not found in ratings_df.")
        if rating_value_column not in ratings_df.columns:
            raise ValueError(f"Rating value column '{rating_value_column}' not found in ratings_df.")

        if text_id_column not in df.columns:
            raise ValueError(f"Text ID column '{text_id_column}' not found in main DataFrame.")

        # Get set of available ratings
        available_ids = set(ratings_df[rating_id_column].dropna().unique())

        # Identify missing
        missing_mask = ~df[text_id_column].isin(available_ids)
        missing_df = df[missing_mask]

        for idx, row in missing_df.iterrows():
            exclusions.append({
                "index": int(idx),
                "conversation_id": str(row[text_id_column]),
                "reason": "missing_rating"
            })

        valid_df = df[~missing_mask].copy()

    # Case 2: Ratings are a column in the main DataFrame (e.g., merged already)
    else:
        if rating_value_column not in df.columns:
            raise ValueError(f"Rating value column '{rating_value_column}' not found in DataFrame and no ratings_df provided.")

        missing_mask = df[rating_value_column].isna()
        missing_df = df[missing_mask]

        for idx, row in missing_df.iterrows():
            cid = row.get(text_id_column, "unknown")
            exclusions.append({
                "index": int(idx),
                "conversation_id": str(cid),
                "reason": "missing_rating"
            })

        valid_df = df[~missing_mask].copy()

    if exclusions:
        logger.error(f"CRITICAL: Detected {len(exclusions)} rows missing ratings.")
    else:
        logger.info("All rows have valid ratings.")

    return valid_df, exclusions


def handle_edge_cases(
    text_df: pd.DataFrame,
    ratings_df: Optional[pd.DataFrame] = None,
    log_dir: Optional[Path] = None,
    min_words: int = MIN_WORD_COUNT
) -> pd.DataFrame:
    """
    Orchestrates edge case detection.
    1. Detects short/empty texts.
    2. Detects missing ratings.
    3. Logs exclusions if log_dir is provided.
    4. HALTS the pipeline if missing ratings are found (FR-007).

    Args:
        text_df: DataFrame with text data (and potentially ratings).
        ratings_df: Optional separate DataFrame with ratings.
        log_dir: Directory to write exclusion logs.
        min_words: Minimum word count threshold.

    Returns:
        Cleaned DataFrame (only if no missing ratings found).

    Raises:
        SystemExit: If missing ratings are detected.
    """
    global MIN_WORD_COUNT
    original_min = MIN_WORD_COUNT
    MIN_WORD_COUNT = min_words

    try:
        # 1. Check for short texts
        text_df, text_exclusions = detect_empty_or_short_texts(text_df, text_column="text_content")

        # 2. Check for missing ratings
        # If ratings_df is provided, we assume we need to merge or check IDs.
        # If not, we check if 'authenticity_score' exists in text_df.
        clean_df, rating_exclusions = detect_missing_ratings(
            text_df,
            ratings_df=ratings_df,
            text_id_column="conversation_id",
            rating_id_column="conversation_id",
            rating_value_column="authenticity_score"
        )

        # 3. Log exclusions
        if log_dir:
            all_exclusions = text_exclusions + rating_exclusions
            if all_exclusions:
                log_exclusions(all_exclusions, log_dir)

        # 4. HALT if missing ratings
        if rating_exclusions:
            logger.error("Pipeline HALT: Missing ratings detected. Aborting execution.")
            sys.exit(1)

        return clean_df

    finally:
        MIN_WORD_COUNT = original_min


def get_exclusion_summary(exclusions: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Generate a summary count of exclusion reasons.

    Args:
        exclusions: List of exclusion dictionaries.

    Returns:
        Dictionary mapping reason to count.
    """
    summary: Dict[str, int] = {}
    for item in exclusions:
        reason = item.get("reason", "unknown")
        summary[reason] = summary.get(reason, 0) + 1
    return summary


def main():
    """
    CLI entry point for testing the edge case handler.
    Expects a CSV file with text and optional ratings.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Edge Case Handler")
    parser.add_argument("--input", type=str, required=True, help="Path to input CSV")
    parser.add_argument("--ratings", type=str, required=False, help="Path to ratings CSV (optional)")
    parser.add_argument("--log-dir", type=str, default="data/logs", help="Directory for logs")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    try:
        df = pd.read_csv(args.input)
        ratings = pd.read_csv(args.ratings) if args.ratings else None
        log_dir = Path(args.log_dir)

        logger.info(f"Loaded {len(df)} rows from {args.input}")
        if ratings is not None:
            logger.info(f"Loaded {len(ratings)} ratings from {args.ratings}")

        result_df = handle_edge_cases(df, ratings_df=ratings, log_dir=log_dir)
        logger.info(f"Pipeline continued. Remaining rows: {len(result_df)}")

    except SystemExit as e:
        logger.critical(f"Pipeline halted with code {e.code}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise


if __name__ == "__main__":
    main()
