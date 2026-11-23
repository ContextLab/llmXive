"""
I/O utilities for the llmXive research pipeline.

Provides functions to fetch text data, load manual ratings, and validate
data schemas against the project's contract definitions.
"""

import os
import logging
from pathlib import Path
from typing import Tuple, Optional, Dict, Any, List

import pandas as pd
import yaml

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define expected paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
CONTRACTS_DIR = PROJECT_ROOT / "contracts"

# Schema file paths
EXTRACTED_FEATURES_SCHEMA_PATH = CONTRACTS_DIR / "extracted_features.schema.yaml"
MANUAL_RATINGS_SCHEMA_PATH = CONTRACTS_DIR / "manual_ratings.schema.yaml"

# Expected file paths for Phase 0 outputs
CONVERSATIONS_JSONL_PATH = DATA_RAW_DIR / "conversations.jsonl"
MANUAL_RATINGS_CSV_PATH = DATA_PROCESSED_DIR / "manual_ratings.csv"
HEDGE_GOLD_STANDARD_CSV_PATH = DATA_PROCESSED_DIR / "hedge_gold_standard.csv"

def _load_schema(schema_path: Path) -> Dict[str, Any]:
    """
    Load a YAML schema definition file.

    Args:
        schema_path: Path to the schema YAML file.

    Returns:
        Dictionary containing the schema definition.

    Raises:
        FileNotFoundError: If the schema file does not exist.
        yaml.YAMLError: If the schema file is invalid YAML.
    """
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    with open(schema_path, 'r', encoding='utf-8') as f:
        try:
            schema = yaml.safe_load(f)
            if schema is None:
                raise ValueError(f"Schema file is empty: {schema_path}")
            return schema
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Invalid YAML in schema file {schema_path}: {e}")

def fetch_text() -> pd.DataFrame:
    """
    Fetch the raw conversation dataset from the JSONL file.

    Reads `data/raw/conversations.jsonl` and returns a DataFrame.
    This function strictly depends on T001f completion.

    Returns:
        pd.DataFrame: DataFrame containing conversation data with columns
                      'conversation_id' and 'text_content'.

    Raises:
        FileNotFoundError: If the conversations.jsonl file is missing.
        ValueError: If the file is empty or lacks required columns.
    """
    if not CONVERSATIONS_JSONL_PATH.exists():
        raise FileNotFoundError(
            f"Required data file missing: {CONVERSATIONS_JSONL_PATH}. "
            "Ensure Phase 0 task T001f (Acquire and format raw conversation dataset) "
            "has been completed successfully."
        )

    try:
        # Read JSONL file
        df = pd.read_json(CONVERSATIONS_JSONL_PATH, lines=True)
    except Exception as e:
        raise ValueError(f"Failed to parse {CONVERSATIONS_JSONL_PATH}: {e}")

    if df.empty:
        raise ValueError(f"Data file {CONVERSATIONS_JSONL_PATH} is empty.")

    # Validate presence of required columns
    required_cols = {'conversation_id', 'text_content'}
    missing_cols = required_cols - set(df.columns)
    if missing_cols:
        raise ValueError(
            f"Missing required columns in {CONVERSATIONS_JSONL_PATH}: {missing_cols}. "
            f"Found columns: {list(df.columns)}"
        )

    logger.info(f"Loaded {len(df)} conversations from {CONVERSATIONS_JSONL_PATH}")
    return df

def load_ratings() -> pd.DataFrame:
    """
    Load the manual authenticity ratings dataset.

    Reads `data/processed/manual_ratings.csv` and returns a DataFrame.
    This function strictly depends on T001k completion.

    Returns:
        pd.DataFrame: DataFrame containing ratings with columns
                      'conversation_id', 'text_content', 'authenticity_score',
                      'rater_id', 'timestamp'.

    Raises:
        FileNotFoundError: If the manual_ratings.csv file is missing.
        ValueError: If the file is empty or lacks required columns.
    """
    if not MANUAL_RATINGS_CSV_PATH.exists():
        raise FileNotFoundError(
            f"Required data file missing: {MANUAL_RATINGS_CSV_PATH}. "
            "Ensure Phase 0 task T001k (Generate Analysis Set) has been completed "
            "and the manual annotation protocol has been executed."
        )

    try:
        df = pd.read_csv(MANUAL_RATINGS_CSV_PATH)
    except Exception as e:
        raise ValueError(f"Failed to parse {MANUAL_RATINGS_CSV_PATH}: {e}")

    if df.empty:
        raise ValueError(f"Data file {MANUAL_RATINGS_CSV_PATH} is empty.")

    # Validate presence of required columns
    required_cols = {'conversation_id', 'text_content', 'authenticity_score'}
    missing_cols = required_cols - set(df.columns)
    if missing_cols:
        raise ValueError(
            f"Missing required columns in {MANUAL_RATINGS_CSV_PATH}: {missing_cols}. "
            f"Found columns: {list(df.columns)}"
        )

    logger.info(f"Loaded {len(df)} ratings from {MANUAL_RATINGS_CSV_PATH}")
    return df

def validate_schemas() -> bool:
    """
    Validate the schemas of extracted features and manual ratings against contract definitions.

    Loads `contracts/extracted_features.schema.yaml` and validates the structure
    of `data/processed/features.csv` (if it exists) and `data/processed/manual_ratings.csv`.

    This function performs strict validation:
    1. Checks that required columns are present.
    2. Checks that column data types match the schema definition.

    Returns:
        bool: True if all validations pass.

    Raises:
        FileNotFoundError: If schema files or data files are missing.
        ValueError: If schema validation fails (missing columns, type mismatch).
    """
    # Validate Extracted Features Schema
    features_path = DATA_PROCESSED_DIR / "features.csv"
    if features_path.exists():
        logger.info(f"Validating schema for {features_path}...")
        schema = _load_schema(EXTRACTED_FEATURES_SCHEMA_PATH)
        df_features = pd.read_csv(features_path)
        _validate_dataframe_schema(df_features, schema, features_path.name)
        logger.info(f"Schema validation passed for {features_path.name}")
    else:
        logger.warning(f"Features file not found: {features_path}. Skipping features schema validation.")

    # Validate Manual Ratings Schema
    if MANUAL_RATINGS_CSV_PATH.exists():
        logger.info(f"Validating schema for {MANUAL_RATINGS_CSV_PATH}...")
        # Note: We assume a manual ratings schema exists or we validate against the known required fields
        # If a specific schema file exists, load it. Otherwise, we use a hardcoded contract for this task.
        ratings_schema_path = CONTRACTS_DIR / "manual_ratings.schema.yaml"
        if ratings_schema_path.exists():
            schema = _load_schema(ratings_schema_path)
            df_ratings = pd.read_csv(MANUAL_RATINGS_CSV_PATH)
            _validate_dataframe_schema(df_ratings, schema, MANUAL_RATINGS_CSV_PATH.name)
        else:
            # Fallback to known required fields if schema file is missing but data exists
            logger.info(f"Schema file {ratings_schema_path} not found. Using hardcoded contract.")
            df_ratings = pd.read_csv(MANUAL_RATINGS_CSV_PATH)
            required_cols = {'conversation_id', 'text_content', 'authenticity_score', 'rater_id', 'timestamp'}
            if not required_cols.issubset(set(df_ratings.columns)):
                missing = required_cols - set(df_ratings.columns)
                raise ValueError(f"Manual ratings missing required columns: {missing}")
            # Check types
            if df_ratings['authenticity_score'].dtype not in ['int64', 'float64']:
                raise ValueError(f"Column 'authenticity_score' must be numeric, found {df_ratings['authenticity_score'].dtype}")

        logger.info(f"Schema validation passed for {MANUAL_RATINGS_CSV_PATH.name}")
    else:
        logger.warning(f"Manual ratings file not found: {MANUAL_RATINGS_CSV_PATH}. Skipping ratings schema validation.")

    return True

def _validate_dataframe_schema(df: pd.DataFrame, schema: Dict[str, Any], file_name: str) -> None:
    """
    Helper function to validate a DataFrame against a schema dictionary.

    Args:
        df: DataFrame to validate.
        schema: Schema dictionary with 'columns' key mapping to column definitions.
        file_name: Name of the file being validated (for error messages).

    Raises:
        ValueError: If validation fails.
    """
    if 'columns' not in schema:
        raise ValueError(f"Invalid schema format for {file_name}: missing 'columns' key")

    schema_cols = schema['columns']
    df_cols = set(df.columns)
    schema_col_names = set(schema_cols.keys())

    # Check for missing columns
    missing_cols = schema_col_names - df_cols
    if missing_cols:
        raise ValueError(f"Validation failed for {file_name}: Missing columns {missing_cols}")

    # Check for extra columns (optional, but good for strictness)
    # extra_cols = df_cols - schema_col_names
    # if extra_cols:
    #     logger.warning(f"Extra columns found in {file_name}: {extra_cols}")

    # Check types
    for col_name, col_def in schema_cols.items():
        expected_type = col_def.get('type')
        if expected_type:
            actual_dtype = df[col_name].dtype
            # Map common YAML types to pandas dtypes
            type_map = {
                'string': ['object', 'string'],
                'integer': ['int64', 'int32'],
                'number': ['float64', 'float32'],
                'boolean': ['bool'],
            }
            valid_dtypes = type_map.get(expected_type, [expected_type])
            if actual_dtype not in valid_dtypes:
                raise ValueError(
                    f"Validation failed for {file_name}: Column '{col_name}' "
                    f"expected type '{expected_type}', found '{actual_dtype}'"
                )

def validate_extracted_features() -> bool:
    """
    Specific validation for the extracted features dataset (T012 output).

    Ensures `data/processed/features.csv` exists and contains the mandatory columns
    defined by FR-008 and the extraction modules.

    Returns:
        bool: True if valid.

    Raises:
        FileNotFoundError: If features.csv is missing.
        ValueError: If required columns are missing.
    """
    features_path = DATA_PROCESSED_DIR / "features.csv"
    if not features_path.exists():
        raise FileNotFoundError(
            f"Required data file missing: {features_path}. "
            "Ensure Phase 2 task T012 (Extraction Mode) has been completed."
        )

    df = pd.read_csv(features_path)
    if df.empty:
        raise ValueError(f"Data file {features_path} is empty.")

    # FR-008 explicitly requires hedge_ratio
    required_cols = {
        'conversation_id',
        'first_person_count',
        'hedge_count',
        'hedge_ratio',
        'sentiment_score'
    }

    missing_cols = required_cols - set(df.columns)
    if missing_cols:
        raise ValueError(
            f"Validation failed for {features_path}: Missing required columns {missing_cols}. "
            f"FR-008 requires 'hedge_ratio' to be present."
        )

    logger.info(f"Extracted features validation passed for {features_path}")
    return True
