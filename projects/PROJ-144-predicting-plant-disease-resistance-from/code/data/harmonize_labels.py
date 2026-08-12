import os
import glob
import pandas as pd
import numpy as np
from typing import Dict, Any
from pathlib import Path
import logging
import json

# Import constants from the project's utility module
try:
    from code.utils.constants import DATA_RAW_DIR, DATA_PROCESSED_DIR, RESULTS_DIR
except ImportError:
    # Fallback for execution context where code is root
    from utils.constants import DATA_RAW_DIR, DATA_PROCESSED_DIR, RESULTS_DIR

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def harmonize_labels(raw_labels_path: str) -> pd.DataFrame:
    """
    Harmonize resistance labels from raw data.
    
    This function:
    1. Loads the raw labels CSV.
    2. Encodes resistance as a binary label (0: Susceptible, 1: Resistant) based on thresholds.
    3. Applies z-scoring to continuous scores for exploratory correlation (harmonized_score).
    4. Validates that binary_label is ready for the trainer.
    
    Args:
        raw_labels_path: Path to the raw labels CSV file.
        
    Returns:
        pd.DataFrame: DataFrame containing 'germplasm_id', 'binary_label', 'harmonized_score',
                      and original metadata.
    """
    if not os.path.exists(raw_labels_path):
        raise FileNotFoundError(f"Raw labels file not found: {raw_labels_path}")
    
    logger.info(f"Loading raw labels from {raw_labels_path}")
    df = pd.read_csv(raw_labels_path)
    
    # Ensure required columns exist
    required_cols = ['germplasm_id', 'assay_score']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in labels: {missing_cols}")
    
    # 1. Encode binary label (FR-003, FR-013)
    # Heuristic: If assay_score > 0.5 (normalized 0-1) or > median, classify as Resistant (1)
    # If the data is not normalized, we assume a threshold or use the median as a robust split.
    # For this implementation, we assume assay_score is a continuous measure of resistance.
    # We use the median to create a balanced binary split if no absolute threshold is provided.
    median_score = df['assay_score'].median()
    
    logger.info(f"Calculating binary label threshold (median): {median_score}")
    df['binary_label'] = (df['assay_score'] >= median_score).astype(int)
    
    # 2. Apply z-scoring for exploratory correlation (FR-013)
    # Only z-score if variance > 0
    if df['assay_score'].std() > 0:
        df['harmonized_score'] = (df['assay_score'] - df['assay_score'].mean()) / df['assay_score'].std()
    else:
        logger.warning("Zero variance in assay_score, setting harmonized_score to 0.")
        df['harmonized_score'] = 0.0
    
    # 3. Validation: Ensure binary_label is suitable for trainer
    # Check for class balance (warn if extremely skewed)
    label_counts = df['binary_label'].value_counts()
    logger.info(f"Class distribution: {label_counts.to_dict()}")
    if len(label_counts) == 1:
        raise ValueError("All samples have the same label. Cannot train a binary classifier.")
    
    # 4. Save intermediate validation report
    validation_report = {
        "source_file": raw_labels_path,
        "total_samples": len(df),
        "median_threshold": float(median_score),
        "class_distribution": {int(k): int(v) for k, v in label_counts.items()},
        "status": "harmonized"
    }
    
    # Ensure output directory exists
    os.makedirs(RESULTS_DIR, exist_ok=True)
    report_path = os.path.join(RESULTS_DIR, "label_harmonization_report.json")
    with open(report_path, 'w') as f:
        json.dump(validation_report, f, indent=2)
    logger.info(f"Saved harmonization report to {report_path}")
    
    return df

def main():
    """
    Main entry point for the harmonize_labels script.
    Reads raw labels, harmonizes them, and saves the processed labels to data/processed/labels.csv.
    """
    # Locate raw labels file
    # We expect the raw data to be in data/raw/ based on T012/T013 output structure
    raw_dir = Path(DATA_RAW_DIR)
    if not raw_dir.exists():
        raise FileNotFoundError(f"Raw data directory not found: {raw_dir}")
    
    # Find labels file (assuming it's named 'labels.csv' or similar in raw)
    label_files = list(raw_dir.glob("*labels*.csv"))
    if not label_files:
        # Fallback: try to find any CSV that might contain labels if naming is different
        all_csvs = list(raw_dir.glob("*.csv"))
        if all_csvs:
            label_files = all_csvs
            logger.warning(f"Could not find specific labels file, using first CSV: {all_csvs[0]}")
        else:
            raise FileNotFoundError("No CSV files found in raw data directory.")
    
    # Process the first found label file (or specific one if known)
    # In a real pipeline, we might iterate or pick based on study ID
    raw_path = label_files[0]
    logger.info(f"Processing labels from: {raw_path}")
    
    try:
        harmonized_df = harmonize_labels(str(raw_path))
        
        # Save processed labels
        os.makedirs(DATA_PROCESSED_DIR, exist_ok=True)
        output_path = os.path.join(DATA_PROCESSED_DIR, "labels.csv")
        harmonized_df.to_csv(output_path, index=False)
        logger.info(f"Saved harmonized labels to {output_path}")
        
        # Log artifact hash (T005 integration)
        try:
            from code.utils.io import compute_file_hash, log_artifact
            file_hash = compute_file_hash(output_path)
            log_artifact(output_path, file_hash)
            logger.info(f"Logged artifact hash: {file_hash}")
        except ImportError:
            logger.warning("Could not import io utilities for logging. Skipping hash log.")
            
    except Exception as e:
        logger.error(f"Failed to harmonize labels: {e}")
        raise

if __name__ == "__main__":
    main()
