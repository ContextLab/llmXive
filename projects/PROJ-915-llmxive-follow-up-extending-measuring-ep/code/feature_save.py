import os
import csv
import logging
import sys
from pathlib import Path
import pandas as pd

from config import get_config

def ensure_feature_data_exists(features_file: Path) -> bool:
    """Ensure feature data exists."""
    return features_file.exists()

def ensure_validation_data_exists(validation_file: Path) -> bool:
    """Ensure validation data exists."""
    return validation_file.exists()

def merge_and_save_features(features_file: Path, responses_file: Path, output_file: Path) -> None:
    """Merge features and responses."""
    if not ensure_feature_data_exists(features_file):
        raise FileNotFoundError(f"Features file not found: {features_file}")
    if not ensure_validation_data_exists(responses_file):
        raise FileNotFoundError(f"Responses file not found: {responses_file}")
    
    features_df = pd.read_csv(features_file)
    responses_df = pd.read_csv(responses_file)
    
    merged = pd.merge(features_df, responses_df, on="prompt_id", how="inner")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(output_file, index=False)
    logging.info(f"Merged and saved to {output_file}")

def run_feature_save_pipeline() -> None:
    """Run feature save pipeline."""
    merge_and_save_features(
        Path("data/processed/features.csv"),
        Path("data/interim/responses.csv"),
        Path("data/interim/merged_features_responses.csv")
    )

def main():
    """Entry point for feature save script."""
    run_feature_save_pipeline()

if __name__ == "__main__":
    main()