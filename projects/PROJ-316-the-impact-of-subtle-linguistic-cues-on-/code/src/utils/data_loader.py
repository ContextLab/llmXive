"""
Data loading utilities for the linguistic cues research pipeline.

This module provides functions to fetch conversation text, load human
authenticity ratings, and validate data schemas against project requirements.
"""

import os
import pandas as pd
from pathlib import Path
from typing import Tuple

# Project root relative to this file
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"


def fetch_text() -> pd.DataFrame:
    """
    Fetch conversation text data from the raw dataset.

    Returns:
        pd.DataFrame: DataFrame containing 'conversation_id' and 'text' columns.

    Raises:
        FileNotFoundError: If the raw conversation data file is not found.
        ValueError: If the expected columns are missing in the source file.
    """
    # Expected raw data file path (created by T001c/T001a process)
    raw_data_path = DATA_RAW_DIR / "conversations.jsonl"

    # Fallback: Check if a CSV version exists (common in some datasets)
    if not raw_data_path.exists():
        csv_path = DATA_RAW_DIR / "conversations.csv"
        if csv_path.exists():
            raw_data_path = csv_path
        else:
            raise FileNotFoundError(
                f"Raw conversation data not found. Expected at: "
                f"{DATA_RAW_DIR / 'conversations.jsonl'} or "
                f"{DATA_RAW_DIR / 'conversations.csv'}. "
                f"Please ensure T001c has completed successfully."
            )

    if raw_data_path.suffix == ".jsonl":
        df = pd.read_json(raw_data_path, lines=True)
    else:
        df = pd.read_csv(raw_data_path)

    # Validate expected columns
    required_cols = {"conversation_id", "text"}
    if not required_cols.issubset(df.columns):
        raise ValueError(
            f"Conversation data missing required columns. "
            f"Found: {list(df.columns)}, Required: {required_cols}"
        )

    # Ensure types
    df['conversation_id'] = df['conversation_id'].astype(str)
    df['text'] = df['text'].astype(str)

    return df


def load_ratings() -> pd.DataFrame:
    """
    Load human authenticity ratings from the processed data directory.

    Returns:
        pd.DataFrame: DataFrame containing 'conversation_id', 'authenticity_score',
                      and 'rater_id' columns.

    Raises:
        FileNotFoundError: If ratings.csv is missing (T001c not completed).
        ValueError: If schema does not match requirements.
    """
    ratings_path = DATA_PROCESSED_DIR / "ratings.csv"

    if not ratings_path.exists():
        raise FileNotFoundError(
            f"Ratings file not found at {ratings_path}. "
            f"Phase 0 (T001c) must complete before this function can run. "
            f"Ensure data/processed/ratings.csv exists with columns: "
            f"conversation_id, authenticity_score, rater_id."
        )

    df = pd.read_csv(ratings_path)

    # Validate schema
    validate_schemas(ratings_path)

    return df


def validate_schemas(ratings_path: Path = None) -> bool:
    """
    Validate that the ratings data exists and matches the required schema.

    Args:
        ratings_path: Optional path to the ratings file. If None, uses default.

    Returns:
        bool: True if validation passes.

    Raises:
        FileNotFoundError: If the ratings file is missing.
        ValueError: If schema columns are missing or types are incorrect.
    """
    if ratings_path is None:
        ratings_path = DATA_PROCESSED_DIR / "ratings.csv"

    if not ratings_path.exists():
        raise FileNotFoundError(
            f"Schema validation failed: Ratings file missing at {ratings_path}. "
            f"Task T001c (Phase 0) must be completed first."
        )

    df = pd.read_csv(ratings_path)
    required_columns = ["conversation_id", "authenticity_score", "rater_id"]
    missing_columns = set(required_columns) - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"Schema validation failed: Missing columns {missing_columns}. "
            f"Expected: {required_columns}"
        )

    # Validate data types roughly
    if not pd.api.types.is_numeric_dtype(df["authenticity_score"]):
        raise ValueError(
            "Schema validation failed: 'authenticity_score' must be numeric."
        )

    return True


def merge_features_and_ratings(features_df: pd.DataFrame, ratings_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge feature extraction results with human ratings for analysis.

    Args:
        features_df: DataFrame with 'conversation_id' and linguistic features.
        ratings_df: DataFrame with 'conversation_id' and 'authenticity_score'.

    Returns:
        pd.DataFrame: Merged DataFrame ready for correlation/regression analysis.
    """
    merged = pd.merge(
        features_df,
        ratings_df[['conversation_id', 'authenticity_score']],
        on='conversation_id',
        how='inner'
    )
    return merged