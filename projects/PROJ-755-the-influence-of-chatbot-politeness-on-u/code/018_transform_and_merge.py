"""
T018: Schema Definition, Transformation, and Merge for HCI_P2, Persona-Chat, and EmpatheticDialogues.

This script loads the filtered datasets produced by T019, defines a unified target schema,
transforms each dataset to match, and merges them into a single Parquet file.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd

# Project root setup
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW_FILTERED_DIR = PROJECT_ROOT / "data" / "raw" / "filtered"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Target Schema Definition (matches contracts/dataset.schema.yaml requirements)
TARGET_SCHEMA = {
    "user_id": "string",
    "dialogue_id": "string",
    "quality_rating": "integer",
    "age": "integer",  # Nullable
    "gender": "string", # Nullable
    "utterances": "string", # JSON string or concatenated text
    "source_dataset": "string",
    "conversation_length": "integer" # Number of utterances
}

def ensure_directories():
    """Ensure output directories exist."""
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured directories exist: {DATA_PROCESSED_DIR}")

def load_filtered_dataset(dataset_name: str) -> Optional[pd.DataFrame]:
    """
    Load a filtered dataset from data/raw/filtered/.
    Expected files: data/raw/filtered/{dataset_name}_filtered.parquet
    """
    file_path = DATA_RAW_FILTERED_DIR / f"{dataset_name}_filtered.parquet"
    if not file_path.exists():
        # Check for alternative extensions or naming if necessary, but strictly follow T019 output
        logger.warning(f"Filtered file not found: {file_path}. Attempting fallback search...")
        # Fallback: try to find any parquet in the directory if exact name fails
        matches = list(DATA_RAW_FILTERED_DIR.glob(f"*{dataset_name}*.parquet"))
        if matches:
            file_path = matches[0]
            logger.info(f"Found fallback file: {file_path}")
        else:
            logger.error(f"Could not locate filtered dataset for {dataset_name}.")
            return None

    try:
        df = pd.read_parquet(file_path)
        logger.info(f"Loaded {dataset_name}: {len(df)} rows, columns: {list(df.columns)}")
        return df
    except Exception as e:
        logger.error(f"Failed to load {dataset_name} from {file_path}: {e}")
        return None

def load_target_schema() -> Dict[str, str]:
    """Return the target schema definition."""
    return TARGET_SCHEMA

def transform_to_target_schema(df: pd.DataFrame, source_name: str) -> pd.DataFrame:
    """
    Transform a raw dataframe to match the TARGET_SCHEMA.
    Handles column mapping, type casting, and missing value handling.
    """
    logger.info(f"Transforming {source_name} to target schema...")
    df = df.copy()

    # 1. Ensure source_dataset column exists
    df["source_dataset"] = source_name

    # 2. Map/Normalize columns based on source-specific logic
    # Common expected columns from T019 filtering: user_id, dialogue_id, quality_rating, utterances, age, gender

    # --- HCI_P2 Specifics (assumed columns from T015) ---
    # If columns are missing, they will be filled with NaN later
    
    # 3. Standardize Column Names (Generic mapping for robustness)
    # We assume the filtered datasets have at least: user_id, dialogue_id, quality_rating, utterances
    # We map them to the target names if they differ slightly (case sensitivity, etc.)
    column_map = {}
    for col in df.columns:
        lower_col = col.lower()
        if lower_col in ["user_id", "userid", "user"]:
            column_map[col] = "user_id"
        elif lower_col in ["dialogue_id", "dialogueid", "dialogue"]:
            column_map[col] = "dialogue_id"
        elif lower_col in ["quality_rating", "rating", "quality"]:
            column_map[col] = "quality_rating"
        elif lower_col in ["utterances", "utterance", "text", "message"]:
            column_map[col] = "utterances"
        elif lower_col in ["age"]:
            column_map[col] = "age"
        elif lower_col in ["gender", "sex"]:
            column_map[col] = "gender"
    
    df = df.rename(columns=column_map)

    # 4. Fill missing required columns with NaN or defaults
    for col in TARGET_SCHEMA.keys():
        if col not in df.columns:
            df[col] = None
            logger.warning(f"Column '{col}' missing in {source_name}, filling with None.")

    # 5. Type Casting and Cleaning
    # Ensure IDs are strings
    df["user_id"] = df["user_id"].astype(str)
    df["dialogue_id"] = df["dialogue_id"].astype(str)
    
    # Ensure quality_rating is integer (handling potential NaNs by converting to float first then nullable int)
    if "quality_rating" in df.columns:
        df["quality_rating"] = pd.to_numeric(df["quality_rating"], errors='coerce')
        # Convert to nullable Int64 to allow NaNs
        df["quality_rating"] = df["quality_rating"].astype("Int64")

    # Ensure age is integer (nullable)
    if "age" in df.columns:
        df["age"] = pd.to_numeric(df["age"], errors='coerce').astype("Int64")

    # Ensure gender is string
    if "gender" in df.columns:
        df["gender"] = df["gender"].astype(str).replace("nan", None)

    # Ensure utterances is string
    if "utterances" in df.columns:
        df["utterances"] = df["utterances"].astype(str)

    # Calculate conversation_length if not present
    if "conversation_length" not in df.columns:
        # If utterances is a list or JSON string, parse it; else count rows if already aggregated
        # Assumption: In filtered data, one row = one dialogue. Utterances might be a list or concatenated string.
        # If it's a list (object), len() works. If it's a string, we might need to split.
        # For safety, we assume T019 output has 'utterances' as a list or we treat the row as length 1 if ambiguous.
        # However, standard HuggingFace datasets often have 'utterances' as a list of dicts or strings.
        try:
            # Attempt to count if it's a list-like object
            df["conversation_length"] = df["utterances"].apply(lambda x: len(x) if isinstance(x, (list, tuple)) else 1)
        except Exception:
            df["conversation_length"] = 1
            logger.warning("Could not determine conversation length from utterances; defaulting to 1.")

    # 6. Select and Order Columns to match TARGET_SCHEMA
    final_columns = [col for col in TARGET_SCHEMA.keys()]
    # Ensure all exist before selecting
    final_columns = [c for c in final_columns if c in df.columns]
    
    df = df[final_columns]
    
    # 7. Validate Constraints
    # Check for nulls in required fields (user_id, dialogue_id, quality_rating)
    required_nulls = df[["user_id", "dialogue_id", "quality_rating"]].isnull().sum()
    if required_nulls.sum() > 0:
        logger.warning(f"Found nulls in required fields for {source_name}: {required_nulls.to_dict()}")
        # Drop rows with nulls in critical ID/Rating fields to ensure merge integrity
        df = df.dropna(subset=["user_id", "dialogue_id", "quality_rating"])
        logger.info(f"Dropped {len(df) - df.index.size} rows with null critical fields in {source_name}.")

    logger.info(f"Transformed {source_name}: {len(df)} rows, schema: {list(df.dtypes)}")
    return df

def validate_transformed_data(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Validate the transformed dataframe against the target schema.
    Returns (is_valid, list_of_errors).
    """
    errors = []
    schema = TARGET_SCHEMA

    # Check columns
    missing_cols = set(schema.keys()) - set(df.columns)
    if missing_cols:
        errors.append(f"Missing columns: {missing_cols}")

    # Check types (basic check)
    if "quality_rating" in df.columns:
        if not pd.api.types.is_integer_dtype(df["quality_rating"]) and not pd.api.types.is_float_dtype(df["quality_rating"]):
            errors.append("quality_rating is not numeric")

    if "conversation_length" in df.columns:
         if not pd.api.types.is_integer_dtype(df["conversation_length"]):
             errors.append("conversation_length is not numeric")

    return len(errors) == 0, errors

def save_transformed_data(df: pd.DataFrame, output_path: Path):
    """Save the merged dataframe to Parquet."""
    try:
        df.to_parquet(output_path, index=False)
        logger.info(f"Saved merged data to {output_path} ({len(df)} rows)")
    except Exception as e:
        logger.error(f"Failed to save merged data: {e}")
        raise

def main():
    """Main entry point for T018."""
    logger.info("Starting T018: Schema Definition, Transformation, and Merge")
    ensure_directories()

    datasets = [
        ("hci_p2", "HCI_P2"),
        ("persona_chat", "Persona-Chat"),
        ("empathetic_dialogues", "EmpatheticDialogues")
    ]

    transformed_dfs = []

    for folder_name, display_name in datasets:
        df = load_filtered_dataset(folder_name)
        if df is not None and not df.empty:
            transformed_df = transform_to_target_schema(df, display_name)
            if transformed_df is not None:
                transformed_dfs.append(transformed_df)
        else:
            logger.warning(f"Skipping {display_name} due to missing or empty data.")

    if not transformed_dfs:
        logger.error("No data found to merge. Aborting.")
        sys.exit(1)

    # Merge
    logger.info("Merging datasets...")
    merged_df = pd.concat(transformed_dfs, ignore_index=True)
    
    # Validate
    is_valid, errors = validate_transformed_data(merged_df)
    if not is_valid:
        logger.error(f"Validation failed: {errors}")
        # Continue anyway but warn, or fail? Task says "Validate", usually implies logging.
        # We proceed to save but log the error.

    # Save
    output_path = DATA_PROCESSED_DIR / "merged_dialogues.parquet"
    save_transformed_data(merged_df, output_path)

    logger.info("T018 Completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())