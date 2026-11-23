import argparse
import json
import logging
import os
import sys
from pathlib import Path

import pandas as pd

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    return logging.getLogger(__name__)

def parse_args():
    parser = argparse.ArgumentParser(
        description="T027h: Inject global dominant eigenvalue into features."
    )
    parser.add_argument(
        "--eigenvalue-path",
        type=str,
        default="results/dominant_eigenvalue.json",
        help="Path to the JSON file containing the dominant eigenvalue.",
    )
    parser.add_argument(
        "--features-path",
        type=str,
        default="data/processed/features.json",
        help="Path to the features JSON file to update.",
    )
    parser.add_argument(
        "--output-path",
        type=str,
        default="data/processed/features.json",
        help="Path to write the updated features JSON file.",
    )
    return parser.parse_args()

def load_dominant_eigenvalue(path: Path, logger: logging.Logger) -> float:
    """Load the dominant eigenvalue from the specified JSON file."""
    logger.info(f"Loading dominant eigenvalue from {path}")
    if not path.exists():
        raise FileNotFoundError(f"Eigenvalue file not found: {path}")
    
    with open(path, "r") as f:
        data = json.load(f)
    
    if "dominant_eigenvalue" not in data:
        raise ValueError(f"Key 'dominant_eigenvalue' not found in {path}")
    
    value = float(data["dominant_eigenvalue"])
    logger.info(f"Loaded dominant eigenvalue: {value}")
    return value

def load_features(path: Path, logger: logging.Logger) -> pd.DataFrame:
    """Load features from JSON file into a DataFrame."""
    logger.info(f"Loading features from {path}")
    if not path.exists():
        raise FileNotFoundError(f"Features file not found: {path}")
    
    df = pd.read_json(path)
    logger.info(f"Loaded {len(df)} feature rows")
    return df

def inject_global_feature(df: pd.DataFrame, eigenvalue: float, logger: logging.Logger) -> pd.DataFrame:
    """Append the global eigenvalue as a new column to every row."""
    logger.info(f"Injecting 'global_eigenvalue' column with value {eigenvalue}")
    df["global_eigenvalue"] = eigenvalue
    return df

def save_features(df: pd.DataFrame, path: Path, logger: logging.Logger):
    """Save the updated DataFrame back to JSON."""
    logger.info(f"Saving updated features to {path}")
    # Ensure directory exists
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_json(path, orient="records", indent=2)
    logger.info("Features saved successfully")

def main():
    args = parse_args()
    logger = setup_logging()
    
    eigenvalue_path = Path(args.eigenvalue_path)
    features_path = Path(args.features_path)
    output_path = Path(args.output_path)

    try:
        eigenvalue = load_dominant_eigenvalue(eigenvalue_path, logger)
        df = load_features(features_path, logger)
        df_updated = inject_global_feature(df, eigenvalue, logger)
        save_features(df_updated, output_path, logger)
        logger.info("T027h: Global Feature Injection completed successfully.")
    except Exception as e:
        logger.error(f"Task failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
