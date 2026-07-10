"""
Data Ingestion and Preprocessing Pipeline (US1).

This script implements T014:
- Loads data from raw sources (synthetic or real).
- Performs TPM normalization.
- Handles missing values (imputation).
- Outputs a processed CSV to data/processed/merged_dataset.csv.

Note: This script is designed to be run before T010 (the test) to generate the data
that the test validates.
"""
import os
import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, List

# Add project root to path (two levels up from this file)
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utils.config import get_config
from utils.imputation import impute_missing_values
from utils.validation import validate_data_types, generate_validation_report
from generators.synthetic_data import generate_synthetic_dataset

# Configuration paths (relative to repository root)
RAW_DATA_PATH = project_root / "data" / "raw" / "synthetic_arabidopsis_v1.csv"
OUTPUT_PATH = project_root / "data" / "processed" / "merged_dataset.csv"
VALIDATION_REPORT_PATH = project_root / "data" / "results" / "data_validation_report.json"

def load_raw_data() -> pd.DataFrame:
    """
    Load raw data from the canonical source.
    If the synthetic file doesn't exist, generate it on‑the‑fly using the
    synthetic data generator (T005 logic).
    """
    if not RAW_DATA_PATH.exists():
        # Ensure the raw data directory exists
        RAW_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
        print(f"Raw data not found at {RAW_DATA_PATH}. Generating synthetic dataset...")
        # The generator is expected to write the CSV to RAW_DATA_PATH
        generate_synthetic_dataset(output_path=str(RAW_DATA_PATH))
        if not RAW_DATA_PATH.exists():
            raise RuntimeError(
                f"Synthetic data generation failed to create {RAW_DATA_PATH}."
            )
    df = pd.read_csv(RAW_DATA_PATH)
    return df

def normalize_tpm(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize gene expression counts to TPM (Transcripts Per Million).

    Assumes columns starting with 'gene_' are expression counts.
    """
    # Identify expression columns
    gene_cols = [col for col in df.columns if col.startswith('gene_')]

    if not gene_cols:
        print("Warning: No gene expression columns found starting with 'gene_'. Skipping TPM normalization.")
        return df

    # Calculate sum of counts per sample (row)
    row_sums = df[gene_cols].sum(axis=1)

    # Avoid division by zero
    row_sums = row_sums.replace(0, np.nan)

    # Normalize each gene column
    for col in gene_cols:
        df[col] = (df[col] / row_sums) * 1_000_000

    return df

def process_environmental_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure environmental metadata is properly typed and cleaned.
    """
    env_cols = ['temperature', 'light_intensity', 'humidity']
    for col in env_cols:
        if col in df.columns:
            # Convert to numeric, coercing errors to NaN
            df[col] = pd.to_numeric(df[col], errors='coerce')
    return df

def main():
    """
    Main execution flow for the ingestion pipeline.
    """
    print("Starting Data Ingestion Pipeline (T014)...")

    # 1. Load Data
    print(f"Loading data from {RAW_DATA_PATH}...")
    df = load_raw_data()
    print(f"Loaded {len(df)} rows.")

    # 2. Preprocessing
    print("Normalizing gene expression to TPM...")
    df = normalize_tpm(df)

    print("Cleaning environmental metadata...")
    df = process_environmental_data(df)

    # 3. Imputation (T009 logic)
    # Apply imputation for non‑critical fields.
    # Critical fields (temp, light) are handled by T015 exclusion logic later.
    print("Applying imputation for missing values...")
    df_imputed = impute_missing_values(df, strategy='median')

    # 4. Validation
    print("Validating data types...")
    is_valid, report = validate_data_types(df_imputed)

    # Optionally enrich the report using the helper
    full_report = generate_validation_report(is_valid, report)

    # 5. Save Output
    print(f"Saving processed data to {OUTPUT_PATH}...")
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df_imputed.to_csv(OUTPUT_PATH, index=False)

    # 6. Save Validation Report
    print(f"Saving validation report to {VALIDATION_REPORT_PATH}...")
    VALIDATION_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(VALIDATION_REPORT_PATH, 'w') as f:
        json.dump(full_report, f, indent=2)

    print("Ingestion pipeline completed successfully.")
    return df_imputed

if __name__ == "__main__":
    main()