"""
Data loading utilities for the project.
Provides functions to fetch text, load ratings, and validate schemas.
"""
import os
import pandas as pd
from pathlib import Path
from typing import Tuple

# Define expected paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"

REQUIRED_RATING_COLS = {'conversation_id', 'authenticity_score', 'rater_id', 'timestamp'}


def fetch_text() -> pd.DataFrame:
    """
    Fetches the raw conversation text data.
    Expected input: data/raw/conversations.jsonl
    Returns: DataFrame with 'conversation_id' and 'text_content' columns.
    Raises FileNotFoundError if the source file is missing.
    """
    source_path = DATA_RAW_DIR / "conversations.jsonl"
    if not source_path.exists():
        raise FileNotFoundError(f"Source file not found: {source_path}. "
                                "Please ensure T001c has generated the raw data or T001a found a dataset.")
    
    try:
        df = pd.read_json(source_path, lines=True)
        # Ensure required columns exist
        if 'conversation_id' not in df.columns or 'text_content' not in df.columns:
            raise ValueError(f"Source file {source_path} is missing required columns. "
                             "Expected 'conversation_id' and 'text_content'.")
        return df
    except Exception as e:
        raise RuntimeError(f"Failed to load text data from {source_path}: {e}")


def load_ratings() -> pd.DataFrame:
    """
    Loads the human authenticity ratings.
    Expected input: data/processed/ratings.csv
    Returns: DataFrame with 'conversation_id', 'authenticity_score', 'rater_id', 'timestamp'.
    Raises FileNotFoundError if the file is missing.
    Raises ValueError if the schema is invalid.
    """
    ratings_path = DATA_PROCESSED_DIR / "ratings.csv"
    if not ratings_path.exists():
        raise FileNotFoundError(
            f"Ratings file not found: {ratings_path}. "
            "Phase 0 (T001c) must be completed to generate this file before running analysis."
        )
    
    try:
        df = pd.read_csv(ratings_path)
        validate_schemas(df, is_ratings=True)
        return df
    except FileNotFoundError:
        raise
    except Exception as e:
        raise RuntimeError(f"Failed to load ratings from {ratings_path}: {e}")


def validate_schemas(df: pd.DataFrame, is_ratings: bool = True) -> None:
    """
    Validates the schema of a DataFrame.
    
    Args:
        df: The DataFrame to validate.
        is_ratings: If True, validates against the ratings schema. 
                    If False, validates against the text schema.
                    
    Raises:
        ValueError: If the schema does not match the requirements.
    """
    if is_ratings:
        required_cols = REQUIRED_RATING_COLS
        missing = required_cols - set(df.columns)
        if missing:
            raise ValueError(f"Ratings schema validation failed. Missing columns: {missing}. "
                             f"Required: {required_cols}")
        
        # Validate data types for critical columns
        if 'authenticity_score' in df.columns:
            if not pd.api.types.is_numeric_dtype(df['authenticity_score']):
                raise ValueError("Column 'authenticity_score' must be numeric.")
        
        if 'conversation_id' in df.columns:
            if not pd.api.types.is_string_dtype(df['conversation_id']) and not pd.api.types.is_integer_dtype(df['conversation_id']):
                raise ValueError("Column 'conversation_id' must be string or integer.")
                
    else:
        # Text schema validation
        required_cols = {'conversation_id', 'text_content'}
        missing = required_cols - set(df.columns)
        if missing:
            raise ValueError(f"Text schema validation failed. Missing columns: {missing}. "
                             f"Required: {required_cols}")
        if 'text_content' in df.columns:
            if not pd.api.types.is_string_dtype(df['text_content']):
                raise ValueError("Column 'text_content' must be string.")


def merge_features_and_ratings(features_df: pd.DataFrame, ratings_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merges extracted features with ratings on conversation_id.
    
    Args:
        features_df: DataFrame from feature extraction.
        ratings_df: DataFrame from load_ratings().
                    
    Returns:
        Merged DataFrame.
    """
    if 'conversation_id' not in features_df.columns:
        raise ValueError("Features DataFrame must contain 'conversation_id'.")
    if 'conversation_id' not in ratings_df.columns:
        raise ValueError("Ratings DataFrame must contain 'conversation_id'.")
        
    return pd.merge(features_df, ratings_df, on='conversation_id', how='inner')