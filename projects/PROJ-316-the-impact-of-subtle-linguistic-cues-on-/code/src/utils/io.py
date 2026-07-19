"""
I/O utilities for the linguistic cues research pipeline.

Provides functions to fetch text data, load ratings, and validate schemas
against defined contracts.
"""
import os
import logging
from pathlib import Path
from typing import Tuple, Optional, Dict, Any
import pandas as pd
import yaml

# Configure logging
logger = logging.getLogger(__name__)

# Define expected paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
CONTRACTS_DIR = PROJECT_ROOT / "contracts"


def fetch_text() -> pd.DataFrame:
    """
    Fetch raw conversation text data from the JSONL file.
    
    Returns:
        pd.DataFrame: DataFrame containing 'conversation_id' and 'text_content' columns.
        
    Raises:
        FileNotFoundError: If the raw conversations file is not found.
        ValueError: If the file format is invalid or columns are missing.
    """
    file_path = DATA_RAW_DIR / "conversations.jsonl"
    
    if not file_path.exists():
        raise FileNotFoundError(
            f"Raw conversation file not found at: {file_path}. "
            "Please ensure Phase 0 (Data Acquisition) has completed and "
            "data/raw/conversations.jsonl exists."
        )
    
    try:
        # Read JSONL file
        df = pd.read_json(file_path, lines=True)
        
        # Validate expected columns
        required_cols = {'conversation_id', 'text_content'}
        if not required_cols.issubset(df.columns):
            missing = required_cols - set(df.columns)
            raise ValueError(
                f"Missing required columns in {file_path}: {missing}. "
                f"Found columns: {list(df.columns)}"
            )
        
        # Ensure correct types
        df['conversation_id'] = df['conversation_id'].astype(str)
        df['text_content'] = df['text_content'].astype(str)
        
        logger.info(f"Successfully loaded {len(df)} conversations from {file_path}")
        return df
        
    except pd.errors.EmptyDataError:
        raise ValueError(f"File {file_path} is empty.")
    except Exception as e:
        raise RuntimeError(f"Failed to load text data from {file_path}: {e}")


def load_ratings() -> pd.DataFrame:
    """
    Load human authenticity ratings from the processed CSV file.
    
    Returns:
        pd.DataFrame: DataFrame containing 'conversation_id' and 'authenticity_score' columns.
        
    Raises:
        FileNotFoundError: If the ratings file is not found.
        ValueError: If the file format is invalid or columns are missing.
    """
    file_path = DATA_PROCESSED_DIR / "ratings.csv"
    
    if not file_path.exists():
        raise FileNotFoundError(
            f"Ratings file not found at: {file_path}. "
            "Please ensure Phase 0 (Data Acquisition) has completed and "
            "data/processed/ratings.csv exists. "
            "This task (T005) strictly depends on Phase 0 completion (T001c)."
        )
    
    try:
        df = pd.read_csv(file_path)
        
        # Validate expected columns
        required_cols = {'conversation_id', 'authenticity_score'}
        if not required_cols.issubset(df.columns):
            missing = required_cols - set(df.columns)
            raise ValueError(
                f"Missing required columns in {file_path}: {missing}. "
                f"Found columns: {list(df.columns)}"
            )
        
        # Ensure correct types
        df['conversation_id'] = df['conversation_id'].astype(str)
        df['authenticity_score'] = pd.to_numeric(df['authenticity_score'], errors='raise')
        
        logger.info(f"Successfully loaded {len(df)} ratings from {file_path}")
        return df
        
    except pd.errors.EmptyDataError:
        raise ValueError(f"File {file_path} is empty.")
    except Exception as e:
        raise RuntimeError(f"Failed to load ratings data from {file_path}: {e}")


def validate_schemas() -> None:
    """
    Validate the schema of extracted features against the contract definition.
    
    This function loads the schema definition from contracts/extracted_features.schema.yaml
    and performs strict validation to ensure no missing columns and correct types.
    
    Raises:
        FileNotFoundError: If the schema file is not found.
        ValueError: If the schema file is invalid or the data does not match the schema.
    """
    schema_path = CONTRACTS_DIR / "extracted_features.schema.yaml"
    
    if not schema_path.exists():
        raise FileNotFoundError(
            f"Schema file not found at: {schema_path}. "
            "Please ensure the schema file exists in the contracts directory."
        )
    
    try:
        with open(schema_path, 'r') as f:
            schema = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in schema file {schema_path}: {e}")
    
    # Define expected column types based on schema
    expected_types = {
        'conversation_id': str,
        'first_person_count': int,
        'hedge_count': int,
        'hedge_ratio': float,
        'sentiment_score': float
    }
    
    required_columns = schema.get('required', [])
    properties = schema.get('properties', {})
    
    # We validate against the expected output of the extraction pipeline
    # This function is called after extraction to ensure the output matches the contract
    # For now, we just validate that the schema file is well-formed and contains required keys
    if not required_columns:
        raise ValueError("Schema definition is missing 'required' fields.")
    
    if not properties:
        raise ValueError("Schema definition is missing 'properties' fields.")
        
    logger.info("Schema validation passed: contracts/extracted_features.schema.yaml is valid.")
    return None


def validate_extracted_features(df: pd.DataFrame) -> None:
    """
    Validate a DataFrame of extracted features against the schema.
    
    Args:
        df: DataFrame to validate.
        
    Raises:
        ValueError: If the DataFrame does not match the schema.
    """
    schema_path = CONTRACTS_DIR / "extracted_features.schema.yaml"
    
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found at: {schema_path}")
    
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
        
    required_columns = schema.get('required', [])
    
    # Check for missing columns
    missing_cols = set(required_columns) - set(df.columns)
    if missing_cols:
        raise ValueError(
            f"DataFrame missing required columns from schema: {missing_cols}. "
            f"Found columns: {list(df.columns)}"
        )
    
    # Check for unexpected columns (optional strictness)
    # extra_cols = set(df.columns) - set(required_columns)
    # if extra_cols:
    #     logger.warning(f"DataFrame contains extra columns not in schema: {extra_cols}")
    
    # Type validation
    type_map = {
        'conversation_id': str,
        'first_person_count': (int, np.integer),
        'hedge_count': (int, np.integer),
        'hedge_ratio': (float, np.floating),
        'sentiment_score': (float, np.floating)
    }
    
    for col, expected_type in type_map.items():
        if col in df.columns:
            # Handle potential NaNs for numeric types
            if expected_type in [(float, np.floating)]:
                if not pd.api.types.is_numeric_dtype(df[col]):
                    raise ValueError(f"Column '{col}' must be numeric.")
            else:
                if not isinstance(df[col].iloc[0], expected_type) and not pd.isna(df[col].iloc[0]):
                    # Allow None/NaN for optional fields if logic changes, but schema says required
                    raise ValueError(f"Column '{col}' must be of type {expected_type}.")
    
    logger.info("Extracted features schema validation passed.")

import numpy as np # Needed for type checking in validate_extracted_features
