"""
I/O utilities for the llmXive research pipeline.

This module provides functions to fetch text data, load ratings, and validate
data schemas as required by the project specifications.
"""

import os
import pandas as pd
from pathlib import Path
from typing import Tuple, Optional


def fetch_text(file_path: Optional[str] = None) -> pd.DataFrame:
    """
    Fetch text data from a JSONL file.

    Args:
        file_path: Path to the JSONL file. Defaults to 'data/raw/conversations.jsonl'.

    Returns:
        DataFrame with columns: conversation_id, text_content

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is empty or malformed.
    """
    if file_path is None:
        file_path = "data/raw/conversations.jsonl"

    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Text data file not found: {path}")

    df = pd.read_json(path, lines=True)

    if df.empty:
        raise ValueError(f"Text data file is empty: {path}")

    required_cols = {"conversation_id", "text_content"}
    if not required_cols.issubset(df.columns):
        missing = required_cols - set(df.columns)
        raise ValueError(f"Text data missing required columns: {missing}")

    return df[["conversation_id", "text_content"]]


def load_ratings(file_path: Optional[str] = None) -> pd.DataFrame:
    """
    Load authenticity ratings from a CSV file.

    Args:
        file_path: Path to the ratings CSV. Defaults to 'data/processed/ratings.csv'.

    Returns:
        DataFrame with columns: conversation_id, authenticity_score, rater_id, timestamp

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is empty or schema mismatched.
    """
    if file_path is None:
        file_path = "data/processed/ratings.csv"

    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(
            f"Ratings file not found: {path}. "
            "Phase 0 (T001c) must complete to generate this file."
        )

    df = pd.read_csv(path)

    if df.empty:
        raise ValueError(f"Ratings file is empty: {path}")

    required_cols = {"conversation_id", "authenticity_score", "rater_id", "timestamp"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(
            f"Ratings file missing required columns: {missing}. "
            f"Expected columns: {required_cols}, found: {set(df.columns)}"
        )

    return df[["conversation_id", "authenticity_score", "rater_id", "timestamp"]]


def validate_schemas(
    text_df: Optional[pd.DataFrame] = None,
    ratings_df: Optional[pd.DataFrame] = None
) -> Tuple[bool, str]:
    """
    Validate that data schemas match project requirements.

    Args:
        text_df: Optional DataFrame of text data to validate.
        ratings_df: Optional DataFrame of ratings data to validate.

    Returns:
        Tuple of (is_valid, message)

    Raises:
        FileNotFoundError: If ratings.csv is missing (hard gate per spec).
    """
    # Hard gate: ratings.csv MUST exist
    ratings_path = Path("data/processed/ratings.csv")
    if not ratings_path.exists():
        raise FileNotFoundError(
            f"CRITICAL: Ratings file missing at {ratings_path}. "
            "Phase 0 (T001c) has not completed. The pipeline halts until "
            "human authenticity ratings are generated."
        )

    # If text_df provided, validate its schema
    if text_df is not None:
        text_required = {"conversation_id", "text_content"}
        text_missing = text_required - set(text_df.columns)
        if text_missing:
            return False, f"Text data missing columns: {text_missing}"

    # If ratings_df provided, validate its schema
    if ratings_df is not None:
        ratings_required = {"conversation_id", "authenticity_score", "rater_id", "timestamp"}
        ratings_missing = ratings_required - set(ratings_df.columns)
        if ratings_missing:
            return False, f"Ratings data missing columns: {ratings_missing}"

    return True, "All schemas validated successfully."