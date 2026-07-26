"""
T016: Save final feature-rich dataset to data/processed/features.csv.

This script loads the extracted features (produced by T014) and the
validation flags (produced by T015), merges them, and writes the final
dataset to the designated output path.

It relies on the existing API surface:
- code/features.py: run_feature_extraction (to generate features if missing)
- code/validation_logic.py: run_t015_validation_pipeline (to generate flags)
- code/config.py: get_config (to resolve paths)
"""
import os
import csv
import logging
import sys
from pathlib import Path

# Import from sibling modules using the provided API surface
from features import run_feature_extraction
from validation_logic import run_t015_validation_pipeline
from config import get_config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def ensure_feature_data_exists(config: dict) -> str:
    """
    Ensures the intermediate features CSV exists.
    If it doesn't exist, runs the feature extraction pipeline (T014).
    Returns the path to the features CSV.
    """
    features_path = config["paths"]["processed"]["features"]
    features_dir = Path(features_path).parent
    features_dir.mkdir(parents=True, exist_ok=True)

    if not os.path.exists(features_path):
        logger.info(f"Features file {features_path} not found. Running feature extraction (T014)...")
        run_feature_extraction(config)
        if not os.path.exists(features_path):
            raise FileNotFoundError(
                f"Feature extraction (T014) did not produce the expected file: {features_path}"
            )
    else:
        logger.info(f"Found existing features file: {features_path}")

    return features_path

def ensure_validation_data_exists(config: dict) -> str:
    """
    Ensures the validation flags CSV exists.
    If it doesn't exist, runs the validation pipeline (T015).
    Returns the path to the validation CSV.
    """
    # T015 output path is typically in data/interim or data/processed depending on spec.
    # Based on T015 description: "flag prompts...". We assume it writes to a known location.
    # Let's assume the validation pipeline writes to a standard location defined in config or hardcode if missing.
    # Looking at T015 description: "Implement data validation logic to flag prompts..."
    # We will assume the output is at data/interim/validation_flags.csv if not specified.
    # However, to be safe, we check the config first.
    validation_path = config["paths"].get("interim", {}).get("validation_flags")
    if not validation_path:
        validation_path = os.path.join(config["paths"]["data_root"], "interim", "validation_flags.csv")

    validation_dir = Path(validation_path).parent
    validation_dir.mkdir(parents=True, exist_ok=True)

    if not os.path.exists(validation_path):
        logger.info(f"Validation flags file {validation_path} not found. Running validation (T015)...")
        run_t015_validation_pipeline(config)
        if not os.path.exists(validation_path):
            raise FileNotFoundError(
                f"Validation pipeline (T015) did not produce the expected file: {validation_path}"
            )
    else:
        logger.info(f"Found existing validation flags file: {validation_path}")

    return validation_path

def merge_and_save_features(features_path: str, validation_path: str, output_path: str):
    """
    Loads features and validation flags, merges them by prompt_id,
    and saves the final result to output_path.
    """
    logger.info(f"Merging data from {features_path} and {validation_path}")

    try:
        import pandas as pd
    except ImportError:
        logger.error("pandas is required for merging. Please ensure it is installed.")
        sys.exit(1)

    df_features = pd.read_csv(features_path)
    df_validation = pd.read_csv(validation_path)

    # Ensure prompt_id is string for consistent merging
    df_features["prompt_id"] = df_features["prompt_id"].astype(str)
    df_validation["prompt_id"] = df_validation["prompt_id"].astype(str)

    # Merge on prompt_id (left join to keep all features)
    df_final = pd.merge(df_features, df_validation, on="prompt_id", how="left")

    # Fill any missing validation flags with False/0 if appropriate
    # Assuming validation flags are boolean or 0/1
    for col in df_validation.columns:
        if col != "prompt_id" and col not in df_features.columns:
            if df_final[col].dtype == 'object':
                df_final[col] = df_final[col].fillna(False)
            else:
                df_final[col] = df_final[col].fillna(0)

    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    df_final.to_csv(output_path, index=False)
    logger.info(f"Successfully saved final feature-rich dataset to {output_path}")
    logger.info(f"Total rows: {len(df_final)}, Columns: {list(df_final.columns)}")

def main():
    config = get_config()
    output_path = config["paths"]["processed"]["features"]

    logger.info(f"Starting T016: Saving final dataset to {output_path}")

    # Step 1: Ensure features exist (T014)
    features_path = ensure_feature_data_exists(config)

    # Step 2: Ensure validation flags exist (T015)
    validation_path = ensure_validation_data_exists(config)

    # Step 3: Merge and save
    merge_and_save_features(features_path, validation_path, output_path)

    logger.info("T016 completed successfully.")

if __name__ == "__main__":
    main()