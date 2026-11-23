import os
import sys
import logging
import pandas as pd
import json
from pathlib import Path
from typing import Optional

# Local imports from utils
from utils.config import (
    get_lod_value,
    get_use_synthetic_data,
    get_raw_path,
    get_processed_path,
    get_results_path,
    get_random_seed,
    get_min_sample_size,
)
from utils.logging_config import get_logger, log_error_context

logger = get_logger(__name__)


class ConfigurationError(Exception):
    """Raised when configuration is missing or invalid."""
    pass


class InsufficientSampleSizeError(Exception):
    """Raised when the sample size is below the required threshold for real data."""
    pass


def estimate_memory_footprint(df: pd.DataFrame) -> int:
    """Estimate memory usage of a DataFrame in bytes."""
    return df.memory_usage(deep=True).sum()


def handle_lod_titers(df: pd.DataFrame, lod_value: float) -> pd.DataFrame:
    """
    Impute missing titer values ('ND', '', or NaN) based on LOD_VALUE.
    If lod_value is None, raises ConfigurationError.
    Imputation strategy: 0.5 * LOD_VALUE.
    """
    if lod_value is None:
        raise ConfigurationError(
            "LOD_VALUE must be explicitly set in config. No default allowed."
        )

    titer_cols = ["titer_baseline", "titer_post"]
    df = df.copy()

    for col in titer_cols:
        if col not in df.columns:
            continue
        # Ensure column is numeric, coercing errors to NaN
        df[col] = pd.to_numeric(df[col], errors="coerce")

        # Identify missing values (NaN or string representations like 'ND')
        # Since we coerced to numeric, 'ND' etc. are already NaN
        mask = df[col].isna()

        if mask.any():
            logger.info(f"Imputing {mask.sum()} missing values in {col} with 0.5 * LOD ({0.5 * lod_value})")
            df.loc[mask, col] = 0.5 * lod_value

    return df


def merge_otu_serology(otu_df: pd.DataFrame, serology_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge OTU table and Serology metadata on subject_id.
    """
    merged = pd.merge(
        otu_df,
        serology_df,
        on="subject_id",
        how="inner"
    )
    logger.info(f"Merged dataset shape: {merged.shape}")
    return merged


def filter_complete_records(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter out subjects where titer_baseline OR titer_post is truly missing (NaN).
    Microbiome columns: '0' is valid, but NaN is not.
    """
    titer_cols = ["titer_baseline", "titer_post"]
    
    # Filter rows where titers are not NaN
    initial_count = len(df)
    df = df.dropna(subset=titer_cols)
    dropped_titer = initial_count - len(df)
    if dropped_titer > 0:
        logger.warning(f"Dropped {dropped_titer} rows due to missing titer values.")

    # Check microbiome columns for NaN (excluding subject_id and titer columns)
    non_taxa_cols = ["subject_id"] + titer_cols
    taxa_cols = [c for c in df.columns if c not in non_taxa_cols]
    
    if taxa_cols:
        initial_count = len(df)
        df = df.dropna(subset=taxa_cols)
        dropped_taxa = initial_count - len(df)
        if dropped_taxa > 0:
            logger.warning(f"Dropped {dropped_taxa} rows due to missing microbiome data.")
    
    return df


def validate_minimum_sample_size(df: pd.DataFrame, use_synthetic: bool) -> None:
    """
    Validate sample size.
    If real data and N < 50, raise InsufficientSampleSizeError.
    If synthetic data, proceed regardless of size.
    """
    n = len(df)
    min_n = get_min_sample_size() # Default 50

    if not use_synthetic and n < min_n:
        logger.error(f"Insufficient sample size for real data: N={n} < {min_n}")
        raise InsufficientSampleSizeError(
            f"Insufficient sample size (N={n}). Execution halted as per Spec Edge Cases."
        )
    
    logger.info(f"Sample size validation passed: N={n}")


def write_assumptions(n: int, use_synthetic: bool, lod_value: float) -> None:
    """
    Write assumptions documentation to data/results/assumptions.md.
    """
    results_path = get_results_path()
    results_path.mkdir(parents=True, exist_ok=True)
    assumptions_file = results_path / "assumptions.md"

    content = f"""# Assumptions and Methodology Notes

## Data Merging and Filtering
- **Merge Key**: `subject_id`
- **Missing Titer Handling**: Rows with missing `titer_baseline` or `titer_post` were dropped.
- **Microbiome Completeness**: Rows with missing taxon abundances (NaN) were dropped. '0' abundance is valid.

## LOD Handling
- **LOD Value Used**: {lod_value}
- **Imputation Strategy**: Missing/ND values in titer columns were imputed as `0.5 * LOD_VALUE`.

## Sample Size Outcome
- **Final Count (N)**: {n}
- **Data Source**: {'Synthetic' if use_synthetic else 'Real'}
- **Validation**: {'Passed' if (use_synthetic or n >= 50) else 'Failed (Halted)'}
"""
    
    with open(assumptions_file, "w") as f:
        f.write(content)
    logger.info(f"Assumptions written to {assumptions_file}")


def write_error_report(error_type: str, count: int, message: str) -> None:
    """
    Write error report to data/results/sampling_error.json and error_log.txt.
    """
    results_path = get_results_path()
    results_path.mkdir(parents=True, exist_ok=True)
    
    error_json_path = results_path / "sampling_error.json"
    error_txt_path = results_path / "error_log.txt"

    error_data = {
        "error_type": error_type,
        "count": count,
        "message": message
    }

    with open(error_json_path, "w") as f:
        json.dump(error_data, f, indent=2)
    
    with open(error_txt_path, "w") as f:
        f.write(message + "\n")
    
    logger.error(f"Error report written to {error_json_path} and {error_txt_path}")


def run_ingestion() -> None:
    """
    Main ingestion logic for T011d: Merge Microbiome and Serology.
    """
    use_synthetic = get_use_synthetic_data()
    
    # Determine input paths
    if use_synthetic:
        otu_path = get_raw_path() / "synthetic_otutable.csv"
        sero_path = get_raw_path() / "synthetic_serology.csv"
        logger.info("Using synthetic data sources.")
    else:
        otu_path = get_raw_path() / "otutable.csv"
        sero_path = get_raw_path() / "serology.csv"
        logger.info("Using real data sources.")

    # Load data
    try:
        otu_df = pd.read_csv(otu_path)
        sero_df = pd.read_csv(sero_path)
    except FileNotFoundError as e:
        logger.critical(f"Input files not found: {e}")
        sys.exit(1)

    # Merge
    merged_df = merge_otu_serology(otu_df, sero_df)

    # Handle LOD
    lod_value = get_lod_value()
    try:
        merged_df = handle_lod_titers(merged_df, lod_value)
    except ConfigurationError as e:
        logger.critical(str(e))
        sys.exit(1)

    # Filter
    filtered_df = filter_complete_records(merged_df)

    # Validate Sample Size
    try:
        validate_minimum_sample_size(filtered_df, use_synthetic)
    except InsufficientSampleSizeError as e:
        write_error_report(
            error_type="InsufficientSampleSize",
            count=len(filtered_df),
            message=str(e)
        )
        sys.exit(1)

    # Write Output
    processed_path = get_processed_path()
    processed_path.mkdir(parents=True, exist_ok=True)
    output_file = processed_path / "cleared.csv"
    
    filtered_df.to_csv(output_file, index=False)
    logger.info(f"Filtered dataset written to {output_file} with {len(filtered_df)} rows.")

    # Write Assumptions
    write_assumptions(len(filtered_df), use_synthetic, lod_value)


def main() -> None:
    """Entry point."""
    run_ingestion()


if __name__ == "__main__":
    main()