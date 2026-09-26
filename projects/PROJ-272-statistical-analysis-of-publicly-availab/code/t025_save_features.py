"""
T025: Save Feature Matrix.
Saves the processed feature matrix to data/processed/features.csv.
"""
import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd
import numpy as np
from config import get_path

logger = logging.getLogger(__name__)

def load_feature_matrix(input_path: Path) -> pd.DataFrame:
    return pd.read_csv(input_path)

def load_cleaned_metadata(input_path: Path) -> pd.DataFrame:
    return pd.read_csv(input_path)

def merge_features_with_metadata(features: pd.DataFrame, metadata: pd.DataFrame) -> pd.DataFrame:
    # Merge on participant_id if available
    if 'participant_id' in features.columns and 'participant_id' in metadata.columns:
        return pd.merge(features, metadata, on='participant_id', how='left')
    return features

def save_feature_matrix(df: pd.DataFrame, output_path: Path) -> None:
    df.to_csv(output_path, index=False)
    logger.info(f"Feature matrix saved to {output_path}")

def update_metadata(metadata: Dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(metadata, f, indent=2)

def main():
    data_processed = get_path("data/processed")
    data_interim = get_path("data/interim")
    
    # Load features from features.py output
    features_file = data_processed / "features.csv"
    if not features_file.exists():
        logger.error("Features file not found. Run features.py first.")
        return
    
    df = load_feature_matrix(features_file)
    
    # Save to final location
    output_path = data_processed / "features.csv"
    save_feature_matrix(df, output_path)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.parse_args()
    main()
