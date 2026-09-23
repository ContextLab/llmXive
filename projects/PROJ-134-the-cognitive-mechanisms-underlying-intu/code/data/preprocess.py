"""
Preprocessing Pipeline (T016-Preprocess-Validate)

This module implements the preprocessing logic for User Story 1.
It maps text stories to VR scenes, assigns salience levels via blend-shape parameters,
and produces the merged preprocessed dataset required for downstream analysis.

Dependencies:
- T044: data/config/unity_blend_shapes.yaml (Configuration)
- T013/T014: data/processed/synthetic_mfq.csv, data/processed/synthetic_logs.csv (Input)

Output:
- data/processed/merged_simulation.csv (Preprocessed Data)
"""
from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import yaml

# Add parent to path for imports if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from code.config import get_path, load_yaml_config
from code.utils.logging import get_logger, log_operation

# Configure paths
CONFIG_PATH = "data/config/unity_blend_shapes.yaml"
# Note: T016-Preprocess-Validate expects merged data from T013/T014 orchestration
# The orchestration (T056-Orch) writes to 'merged_simulation.csv' before this runs
# However, for robustness, we check common intermediate paths if the specific one is missing
MERGED_DATA_PATHS = [
    "data/processed/merged_simulation.csv",
    "data/processed/merged_data.csv",
    "data/processed/synthetic_mfq.csv", # Fallback if merge didn't happen yet
]
PREPROCESSED_OUTPUT_PATH = "data/processed/merged_simulation.csv"

logger = get_logger("preprocess_pipeline")


def load_yaml_config(config_path: str) -> Dict[str, Any]:
    """Load a YAML configuration file."""
    full_path = get_path(config_path)
    if not os.path.exists(full_path):
        raise FileNotFoundError(f"Configuration file not found: {full_path}")
    
    with open(full_path, 'r') as f:
        return yaml.safe_load(f)


def load_blend_shape_config() -> Dict[str, Any]:
    """
    Load the Unity blend shape configuration.
    Validates that the required 'low' and 'high' keys exist.
    """
    config = load_yaml_config(CONFIG_PATH)
    
    # Schema Validation per T044 requirements
    if "low" not in config or "high" not in config:
        raise ValueError(
            f"Invalid blend shape config at {CONFIG_PATH}. "
            "Missing required keys: 'low' and/or 'high'. "
            "Each must contain a 'blend_shape_params' object."
        )
    
    if "blend_shape_params" not in config["low"] or "blend_shape_params" not in config["high"]:
        raise ValueError(
            f"Invalid blend shape config at {CONFIG_PATH}. "
            "Keys 'low' and 'high' must contain 'blend_shape_params'."
        )
    
    logger.info("Blend shape config loaded and validated.")
    return config


def load_merged_data() -> pd.DataFrame:
    """
    Load the merged dataset from the intermediate CSV.
    Tries the primary expected path first, then fallbacks.
    """
    # Try primary path first
    primary_path = get_path(MERGED_DATA_PATHS[0])
    if os.path.exists(primary_path):
        logger.info(f"Loading merged data from {primary_path}")
        return pd.read_csv(primary_path)
    
    # Fallback logic: Try to merge MFQ and Logs manually if the intermediate file is missing
    # This handles cases where T056-Orch might have skipped the merge step or named it differently
    mfq_path = get_path("data/processed/synthetic_mfq.csv")
    logs_path = get_path("data/processed/synthetic_logs.csv")
    
    if os.path.exists(mfq_path) and os.path.exists(logs_path):
        logger.warning("Merged data file not found. Attempting to merge MFQ and Logs on-the-fly.")
        df_mfq = pd.read_csv(mfq_path)
        df_logs = pd.read_csv(logs_path)
        
        # Merge on participant_id
        # Ensure both have participant_id
        if "participant_id" not in df_mfq.columns or "participant_id" not in df_logs.columns:
            raise ValueError("Cannot merge: participant_id missing in source files.")
        
        merged_df = pd.merge(df_mfq, df_logs, on="participant_id", how="inner")
        logger.info(f"Merged {len(df_mfq)} MFQ rows with {len(df_logs)} log rows. Result: {len(merged_df)} rows.")
        return merged_df
    
    # If all else fails
    raise FileNotFoundError(
        f"Merged data file not found at expected path: {primary_path}. "
        f"Also checked fallbacks at {get_path('data/processed/synthetic_mfq.csv')} "
        f"and {get_path('data/processed/synthetic_logs.csv')}. "
        "Ensure T013 and T014 have completed successfully."
    )


def assign_salience_level(story_id: Any, config: Dict[str, Any]) -> str:
    """
    Assign a salience level ('low' or 'high') based on the story_id.
    
    Logic:
    - If story_id is in config['low'], return 'low'.
    - If story_id is in config['high'], return 'high'.
    - If not found, default to 'low' (or raise error depending on strictness).
      Per T044, the config is the single source of truth.
    """
    low_stories = config.get("low", {}).get("story_ids", [])
    high_stories = config.get("high", {}).get("story_ids", [])
    
    # Handle potential float/int types from CSV
    story_id_str = str(story_id)
    
    if story_id_str in [str(s) for s in low_stories]:
        return "low"
    elif story_id_str in [str(s) for s in high_stories]:
        return "high"
    else:
        # Default to low if not explicitly mapped, but log a warning
        logger.warning(f"Story ID '{story_id}' not found in salience mapping. Defaulting to 'low'.")
        return "low"


def map_to_blend_shapes(row: pd.Series, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map a row's story_id to the specific blend shape parameters.
    Returns a dictionary of parameters for that salience level.
    """
    salience = row.get("salience_level")
    if salience not in config:
        # Fallback if salience wasn't assigned correctly
        salience = "low"
        
    params = config[salience].get("blend_shape_params", {})
    return params


def process_salience_mapping(df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
    """
    Apply salience mapping to the dataframe.
    Adds 'salience_level' and 'blend_shape_params' (JSON string) columns.
    """
    if "story_id" not in df.columns:
        # If story_id is missing, we might need to infer it or fail
        # Assuming synthetic logs have story_id. If not, we can't map.
        raise ValueError("Input dataframe missing 'story_id' column required for salience mapping.")
    
    # Apply mapping
    df["salience_level"] = df["story_id"].apply(lambda x: assign_salience_level(x, config))
    
    # Extract blend shape params as JSON string for storage
    # This ensures the data is serializable and matches the schema requirements
    df["blend_shape_params"] = df.apply(
        lambda row: json.dumps(map_to_blend_shapes(row, config)), axis=1
    )
    
    logger.info(f"Salience mapping applied. Distribution: {df['salience_level'].value_counts().to_dict()}")
    return df


def save_preprocessed_data(df: pd.DataFrame, output_path: str) -> None:
    """Save the preprocessed dataframe to CSV."""
    full_path = get_path(output_path)
    # Ensure directory exists
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    
    df.to_csv(full_path, index=False)
    logger.info(f"Preprocessed data saved to {full_path}")


def run_preprocessing_pipeline() -> pd.DataFrame:
    """
    Main entry point for the preprocessing pipeline.
    1. Load config.
    2. Load merged data.
    3. Map salience.
    4. Save output.
    """
    log_operation("START", "T016: Preprocessing Pipeline")
    
    try:
        # 1. Load Config
        config = load_blend_shape_config()
        
        # 2. Load Data
        df = load_merged_data()
        
        # 3. Process
        df_processed = process_salience_mapping(df, config)
        
        # 4. Save
        save_preprocessed_data(df_processed, PREPROCESSED_OUTPUT_PATH)
        
        log_operation("COMPLETE", "T016: Preprocessing Pipeline", output_file=PREPROCESSED_OUTPUT_PATH)
        return df_processed
        
    except Exception as e:
        log_operation("FAILED", "T016: Preprocessing Pipeline", error=str(e))
        raise


def main() -> None:
    """Script entry point."""
    # Ensure logging is initialized
    logger = get_logger("preprocess_main")
    logger.info("Starting preprocessing pipeline (T016-Preprocess-Validate)...")
    
    try:
        df = run_preprocessing_pipeline()
        logger.info(f"Pipeline completed successfully. Processed {len(df)} records.")
    except FileNotFoundError as e:
        logger.error(f"Data file missing: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Configuration or data validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()