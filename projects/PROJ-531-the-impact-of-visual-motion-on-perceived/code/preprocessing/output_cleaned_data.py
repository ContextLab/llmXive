"""
T017: Output cleaned_data.csv with documented scoring method and standardization.

This script reads the preprocessed data, applies standardization (0-1 range)
where appropriate, documents the scoring method in metadata, and writes the
final clean dataset to data/processed/cleaned_data.csv.

Dependencies:
  - preprocessing.preprocess (already implemented in T014/T015)
  - utils.logging_config
  - utils.config
"""
import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

# Import existing utilities
from preprocessing.preprocess import run_preprocessing
from utils.logging_config import get_logger, log_processing_step
from utils.config import ConfigManager

def standardize_column(series: pd.Series, min_val: float = 0.0, max_val: float = 1.0) -> pd.Series:
    """
    Min-Max standardization to [min_val, max_val] range.
    Handles edge cases where min == max (constant column).
    """
    if series.min() == series.max():
        # If constant, return the mean (or min_val)
        return pd.Series([min_val] * len(series), index=series.index)
    
    normalized = (series - series.min()) / (series.max() - series.min())
    return normalized * (max_val - min_val) + min_val

def main():
    logger = get_logger("T017_OutputCleanedData")
    log_processing_step(logger, "Starting T017: Output cleaned_data.csv")

    # Paths
    project_root = Path(__file__).resolve().parent.parent.parent
    data_processed_dir = project_root / "data" / "processed"
    data_processed_dir.mkdir(parents=True, exist_ok=True)

    input_file = data_processed_dir / "preprocessed_data.csv"
    output_file = data_processed_dir / "cleaned_data.csv"
    metadata_file = data_processed_dir / "cleaned_data_metadata.json"

    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        logger.error("Run T014 (preprocess.py) first to generate preprocessed_data.csv")
        raise FileNotFoundError(f"Input file {input_file} not found. Run preprocessing first.")

    logger.info(f"Reading preprocessed data from {input_file}")
    df = pd.read_csv(input_file)

    # Documented scoring method
    scoring_method = {
        "agency_score": {
            "source": "Synthetic generator ground truth (T013)",
            "range": "0-100 scale, standardized to 0-1",
            "description": "Perceived agency score derived from motion features"
        },
        "latency": {
            "source": "Synthetic motion simulation",
            "unit": "milliseconds",
            "standardization": "Min-Max to [0, 1]"
        },
        "smoothness": {
            "source": "Jerk-based calculation",
            "unit": "normalized jerk",
            "standardization": "Min-Max to [0, 1] (higher = smoother)"
        },
        "lead_time": {
            "source": "Predictive motion estimation",
            "unit": "milliseconds",
            "standardization": "Min-Max to [0, 1]"
        }
    }

    logger.info("Applying standardization (0-1 range) to numeric features...")
    
    # Standardize numeric columns (exclude participant_id if present)
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    for col in numeric_cols:
        if col != "participant_id":  # Keep IDs as-is
            original_min = df[col].min()
            original_max = df[col].max()
            df[col] = standardize_column(df[col], min_val=0.0, max_val=1.0)
            logger.debug(f"Standardized {col}: [{original_min}, {original_max}] -> [0, 1]")

    # Ensure all required columns exist
    required_cols = ["participant_id", "latency", "smoothness", "lead_time", "agency_score"]
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        logger.error(f"Missing required columns: {missing_cols}")
        raise ValueError(f"Preprocessed data missing required columns: {missing_cols}")

    # Write output
    logger.info(f"Writing cleaned data to {output_file}")
    df.to_csv(output_file, index=False)

    # Write metadata
    metadata = {
        "file_path": str(output_file.relative_to(project_root)),
        "created_at": datetime.now().isoformat(),
        "n_samples": len(df),
        "n_features": len(required_cols),
        "scoring_method": scoring_method,
        "standardization": {
            "method": "Min-Max normalization",
            "range": [0.0, 1.0],
            "description": "All numeric features scaled to 0-1 range"
        },
        "source_task": "T014 (preprocess.py) + T015 (VIF check)",
        "notes": "Synthetic data stress-test only. No human participants."
    }

    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)

    logger.info(f"T017 complete: {len(df)} rows written to {output_file}")
    logger.info(f"Metadata written to {metadata_file}")
    print(f"SUCCESS: {output_file} created with {len(df)} observations.")

if __name__ == "__main__":
    main()
