import os
import sys
import logging
import pandas as pd
from pathlib import Path
from config import get_config

def load_features(features_file: Path) -> pd.DataFrame:
    """Load features."""
    return pd.read_csv(features_file)

def load_responses(responses_file: Path) -> pd.DataFrame:
    """Load responses."""
    return pd.read_csv(responses_file)

def merge_datasets(features_df: pd.DataFrame, responses_df: pd.DataFrame) -> pd.DataFrame:
    """Merge features and responses."""
    return pd.merge(features_df, responses_df, on="prompt_id", how="inner")

def save_merged_dataset(df: pd.DataFrame, output_path: Path) -> None:
    """Save merged dataset."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)

def run_merge_save_pipeline() -> None:
    """Run merge save pipeline."""
    features_df = load_features(Path("data/processed/features.csv"))
    responses_df = load_responses(Path("data/interim/responses.csv"))
    merged = merge_datasets(features_df, responses_df)
    save_merged_dataset(merged, Path("data/interim/merged_dataset.csv"))

def main():
    """Entry point for merge save script."""
    run_merge_save_pipeline()

if __name__ == "__main__":
    main()