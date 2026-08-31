"""
T018: Schema Definition, Transformation, and Merge for all available datasets.

This script defines the target schema, loads filtered datasets from the three
potential sources (HCI_P2, Persona-Chat, EmpatheticDialogues), transforms them
to the unified schema, and merges them into a single Parquet file.

Target Schema:
  - user_id: str
  - dialogue_id: str
  - quality_rating: float (or int)
  - age: float (or int, nullable)
  - gender: str (or float, nullable)
  - utterances: list of dict (or string representation)
  - source_dataset: str
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_FILTERED_DIR = PROJECT_ROOT / "data" / "raw" / "filtered"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_FILE = PROCESSED_DIR / "merged_dialogues.parquet"

# Target schema definition
TARGET_SCHEMA = {
    "user_id": "str",
    "dialogue_id": "str",
    "quality_rating": "float",
    "age": "float",  # Nullable
    "gender": "str", # Nullable
    "utterances": "object", # List of utterance dicts or string
    "source_dataset": "str"
}

def ensure_directories():
    """Ensure output directories exist."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured directory: {PROCESSED_DIR}")

def load_filtered_dataset(dataset_name: str) -> Optional[pd.DataFrame]:
    """
    Load a filtered dataset from data/raw/filtered/{dataset_name}.
    Handles different source formats.
    """
    source_path = RAW_FILTERED_DIR / dataset_name
    if not source_path.exists():
        logger.warning(f"Dataset source not found: {source_path}. Skipping.")
        return None

    # Determine file format
    parquet_files = list(source_path.glob("*.parquet"))
    csv_files = list(source_path.glob("*.csv"))
    
    if parquet_files:
        # Assume the most recently modified or the only one
        file_path = sorted(parquet_files, key=lambda p: p.stat().st_mtime)[-1]
        logger.info(f"Loading Parquet from: {file_path}")
        df = pd.read_parquet(file_path)
    elif csv_files:
        file_path = sorted(csv_files, key=lambda p: p.stat().st_mtime)[-1]
        logger.info(f"Loading CSV from: {file_path}")
        df = pd.read_csv(file_path)
    else:
        logger.error(f"No valid data files found in {source_path}")
        return None

    if df.empty:
        logger.warning(f"Dataset {dataset_name} is empty after loading.")
        return None

    return df

def load_target_schema() -> Dict[str, str]:
    """Return the target schema definition."""
    return TARGET_SCHEMA

def transform_to_target_schema(df: pd.DataFrame, source_name: str) -> pd.DataFrame:
    """
    Transform a raw/filtered dataframe to the target schema.
    Handles column renaming, type casting, and filling missing columns.
    """
    logger.info(f"Transforming dataset: {source_name} (Shape: {df.shape})")
    
    # Create a copy to avoid modifying original
    new_df = df.copy()

    # 1. Standardize Column Names (Mapping based on common HuggingFace dataset structures)
    # HCI_P2, Persona-Chat, EmpatheticDialogues might have slight variations
    column_mappings = {
        # Common aliases for user_id
        'user': 'user_id',
        'user_id_str': 'user_id',
        # Common aliases for dialogue_id
        'dialogue': 'dialogue_id',
        'dialogue_id_str': 'dialogue_id',
        'conversation_id': 'dialogue_id',
        # Common aliases for quality
        'rating': 'quality_rating',
        'score': 'quality_rating',
        'label': 'quality_rating',
        # Common aliases for demographics
        'user_age': 'age',
        'user_gender': 'gender',
        'gender_label': 'gender',
        # Common aliases for text
        'dialogue_history': 'utterances',
        'chat': 'utterances',
        'conversation': 'utterances',
        'text': 'utterances',
    }

    # Apply renaming
    rename_map = {k: v for k, v in column_mappings.items() if k in new_df.columns}
    if rename_map:
        new_df = new_df.rename(columns=rename_map)
        logger.info(f"Renamed columns: {rename_map}")

    # 2. Ensure Required Columns Exist
    missing_cols = [col for col in TARGET_SCHEMA.keys() if col not in new_df.columns]
    if missing_cols:
        logger.info(f"Adding missing columns with defaults: {missing_cols}")
        for col in missing_cols:
            if col == 'source_dataset':
                new_df[col] = source_name
            elif col == 'utterances':
                new_df[col] = new_df.apply(lambda row: row.to_dict() if not isinstance(row.get('utterances'), (list, dict)) else row.get('utterances'), axis=1)
            else:
                new_df[col] = None # Nullable fields default to None

    # 3. Normalize 'utterances' to a list of strings or dicts if it's a raw string
    if 'utterances' in new_df.columns:
        def normalize_utterances(val):
            if isinstance(val, list):
                return val
            if isinstance(val, str):
                # Try to parse JSON if it looks like a list/dict
                if val.startswith('[') or val.startswith('{'):
                    try:
                        import json
                        return json.loads(val)
                    except json.JSONDecodeError:
                        return [val] # Fallback to single string list
                return [val]
            return [str(val)] if val is not None else []
        
        new_df['utterances'] = new_df['utterances'].apply(normalize_utterances)

    # 4. Type Casting and Cleaning
    # Cast to specific types, allowing NaN for nullable fields
    type_casts = {
        'user_id': str,
        'dialogue_id': str,
        'quality_rating': float,
        'age': float,
        'gender': str,
        'source_dataset': str
    }

    for col, dtype in type_casts.items():
        if col in new_df.columns:
            # Handle potential non-numeric strings in numeric columns
            if dtype in [float, int]:
                new_df[col] = pd.to_numeric(new_df[col], errors='coerce')
            else:
                new_df[col] = new_df[col].astype(dtype, errors='ignore')

    # 5. Filter out rows that are missing mandatory fields (user_id, dialogue_id, quality_rating)
    mandatory_fields = ['user_id', 'dialogue_id', 'quality_rating']
    initial_count = len(new_df)
    new_df = new_df.dropna(subset=mandatory_fields)
    dropped_count = initial_count - len(new_df)
    if dropped_count > 0:
        logger.warning(f"Dropped {dropped_count} rows due to missing mandatory fields in {source_name}.")

    # 6. Ensure source_dataset is set correctly
    new_df['source_dataset'] = source_name

    logger.info(f"Transformed dataset shape: {new_df.shape}")
    return new_df

def validate_transformed_data(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Validate the transformed dataframe against the target schema constraints.
    Returns (is_valid, list_of_errors).
    """
    errors = []
    
    # Check mandatory columns
    for col in ['user_id', 'dialogue_id', 'quality_rating']:
        if col not in df.columns:
            errors.append(f"Missing mandatory column: {col}")
    
    # Check for duplicates (dialogue_id should be unique per source)
    if 'dialogue_id' in df.columns:
        if df['dialogue_id'].duplicated().any():
            errors.append("Duplicate dialogue_id found in merged data.")
    
    # Check data types roughly
    if 'quality_rating' in df.columns:
        if not pd.api.types.is_numeric_dtype(df['quality_rating']):
            errors.append("quality_rating is not numeric.")

    return len(errors) == 0, errors

def save_transformed_data(df: pd.DataFrame):
    """Save the merged dataframe to Parquet."""
    ensure_directories()
    logger.info(f"Saving merged data to: {OUTPUT_FILE}")
    df.to_parquet(OUTPUT_FILE, index=False)
    logger.info(f"Successfully saved {len(df)} rows to {OUTPUT_FILE}")

def main():
    logger.info("Starting T018: Transform and Merge")
    
    # Define potential sources based on task dependencies (T015, T015b, T015c)
    # We look for directories in data/raw/filtered corresponding to these sources
    potential_sources = [
        "hci_p2",
        "persona_chat",
        "empathetic_dialogues"
    ]

    all_dfs = []
    
    for source in potential_sources:
        logger.info(f"Processing source: {source}")
        raw_df = load_filtered_dataset(source)
        if raw_df is not None:
            transformed_df = transform_to_target_schema(raw_df, source)
            if not transformed_df.empty:
                all_dfs.append(transformed_df)
            else:
                logger.warning(f"Transformed data for {source} is empty. Skipping.")
        else:
            logger.info(f"No data found for source: {source}. Skipping.")

    if not all_dfs:
        logger.error("No data found to merge. Exiting.")
        # Create an empty file with schema to indicate failure or empty state?
        # For now, just exit.
        return

    # Merge all dataframes
    logger.info(f"Merging {len(all_dfs)} datasets.")
    merged_df = pd.concat(all_dfs, ignore_index=True)
    
    # Validate
    is_valid, validation_errors = validate_transformed_data(merged_df)
    if not is_valid:
        logger.error(f"Validation failed: {validation_errors}")
        # Decide: Fail loudly or save anyway with warning?
        # Per constraints: "Fail loudly, never silently". But saving is the goal.
        # We log error but proceed if critical data exists, or raise.
        # Let's raise to be safe as per "fail loudly".
        raise ValueError(f"Data validation failed: {validation_errors}")

    # Save
    save_transformed_data(merged_df)
    
    # Generate a simple manifest
    manifest = {
        "task_id": "T018",
        "output_file": str(OUTPUT_FILE.relative_to(PROJECT_ROOT)),
        "total_rows": len(merged_df),
        "sources_included": [df['source_dataset'].iloc[0] for df in all_dfs],
        "schema": TARGET_SCHEMA
    }
    
    manifest_path = PROCESSED_DIR / "merged_manifest.json"
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    logger.info(f"Manifest saved to {manifest_path}")

if __name__ == "__main__":
    main()