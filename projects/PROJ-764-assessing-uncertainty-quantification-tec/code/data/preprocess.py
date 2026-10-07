import os
import sys
import json
import yaml
import pandas as pd
import numpy as np
import pickle
from typing import Dict, List, Tuple, Any
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/pipeline.log')
    ]
)
logger = logging.getLogger(__name__)

def load_config() -> Dict[str, Any]:
    """Load configuration from code/config.yaml."""
    config_path = Path("code/config.yaml")
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def load_data(split_name: str = "all") -> pd.DataFrame:
    """
    Load pre-split data from data/processed/raw_{split}.csv.
    If split_name is "all", load raw_train.csv (assuming PCA is fit on train).
    """
    base_path = Path("data/processed")
    if split_name == "train":
        file_path = base_path / "raw_train.csv"
    elif split_name == "val":
        file_path = base_path / "raw_val.csv"
    elif split_name == "test":
        file_path = base_path / "raw_test.csv"
    else:
        raise ValueError(f"Unknown split: {split_name}")

    if not file_path.exists():
        raise FileNotFoundError(f"Data file not found: {file_path}. "
                                f"Please run T006a/b (preprocess split) first.")

    logger.info(f"Loading data from {file_path}...")
    df = pd.read_csv(file_path)
    logger.info(f"Loaded {len(df)} rows.")
    return df

def load_pca_transformer() -> Any:
    """Load the PCA transformer from data/processed/pca_transformer.pkl."""
    transformer_path = Path("data/processed/pca_transformer.pkl")
    if not transformer_path.exists():
        raise FileNotFoundError(
            f"PCA transformer not found: {transformer_path}. "
            "Please run T006c (PCA Fit) first."
        )
    with open(transformer_path, 'rb') as f:
        return pickle.load(f)

def apply_pca_transform(df: pd.DataFrame, pca: Any, n_components: int = 20) -> Tuple[pd.DataFrame, int, List[str]]:
    """
    Apply PCA transformation to the dataframe.
    Returns transformed DataFrame, count of excluded rows, and list of missing columns.
    """
    # Identify feature columns (exclude target and metadata)
    exclude_cols = ['target_bin', 'formation_energy', 'sample_id']
    feature_cols = [c for c in df.columns if c not in exclude_cols]

    if not feature_cols:
        raise ValueError("No feature columns found in the dataframe.")

    # Check for missing values in feature columns
    missing_mask = df[feature_cols].isnull().any(axis=1)
    excluded_count = missing_mask.sum()
    missing_columns = list(df[feature_cols].columns[df[feature_cols].isnull().any()])

    if excluded_count > 0:
        logger.warning(f"Excluding {excluded_count} rows with missing features.")
        df_clean = df[~missing_mask].copy()
    else:
        df_clean = df.copy()

    if len(df_clean) == 0:
        raise ValueError("No valid rows remaining after exclusion.")

    X = df_clean[feature_cols].values

    # Transform using PCA
    X_transformed = pca.transform(X)

    # Create new DataFrame with PCA components
    pca_col_names = [f'pc_{i+1}' for i in range(X_transformed.shape[1])]
    pca_df = pd.DataFrame(X_transformed, columns=pca_col_names, index=df_clean.index)

    # Preserve target and metadata
    if 'target_bin' in df_clean.columns:
        pca_df['target_bin'] = df_clean['target_bin'].values
    if 'formation_energy' in df_clean.columns:
        pca_df['formation_energy'] = df_clean['formation_energy'].values
    if 'sample_id' in df_clean.columns:
        pca_df['sample_id'] = df_clean['sample_id'].values

    return pca_df, excluded_count, missing_columns

def save_transformed_data(df: pd.DataFrame, output_path: str):
    """Save the transformed DataFrame to CSV."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved transformed data to {output_path}")

def save_validation_report(excluded_count: int, missing_columns: List[str], output_path: str):
    """Save the validation report to JSON."""
    report = {
        "excluded_count": int(excluded_count),
        "missing_columns": missing_columns
    }
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Saved validation report to {output_path}")

def perform_pca_and_exclusion():
    """
    Main function for T006d: PCA Transform & Exclusion.
    Loads PCA transformer, transforms train/val/test sets, excludes missing rows,
    and saves outputs.
    """
    logger.info("Starting PCA Transform & Exclusion (T006d)...")

    # Load PCA transformer
    pca = load_pca_transformer()
    logger.info("PCA transformer loaded successfully.")

    # Verify variance explained
    if hasattr(pca, 'explained_variance_ratio_'):
        total_variance = np.sum(pca.explained_variance_ratio_)
        logger.info(f"PCA explains {total_variance:.4f} of total variance.")
        if total_variance < 0.90:
            logger.warning(f"PCA explains less than 90% variance: {total_variance:.4f}")

    # Process each split
    splits = ['train', 'val', 'test']
    total_excluded = 0
    all_missing_columns = []

    for split in splits:
        logger.info(f"Processing {split} split...")
        df = load_data(split)
        pca_df, excluded_count, missing_cols = apply_pca_transform(df, pca)

        # Save transformed data
        output_path = f"data/processed/features_{split}_20pca.csv"
        save_transformed_data(pca_df, output_path)

        total_excluded += excluded_count
        all_missing_columns.extend(missing_cols)

    # Remove duplicates from missing columns
    unique_missing_columns = list(set(all_missing_columns))

    # Save validation report
    report_path = "data/validation_report.json"
    save_validation_report(total_excluded, unique_missing_columns, report_path)

    logger.info(f"PCA Transform & Exclusion completed. Total excluded: {total_excluded}")
    logger.info(f"Output files created:")
    for split in splits:
        logger.info(f"  - data/processed/features_{split}_20pca.csv")
    logger.info(f"  - data/validation_report.json")

def main():
    """Entry point for the script."""
    try:
        perform_pca_and_exclusion()
        logger.info("Task T006d completed successfully.")
    except Exception as e:
        logger.error(f"Task T006d failed: {e}")
        raise

if __name__ == "__main__":
    main()