import hashlib
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
import numpy as np

from src.exceptions import DataIngestionError, SchemaValidationError
from src.utils.exceptions import InsufficientDataError

logger = logging.getLogger(__name__)

# Configuration for deduplication
# These are the columns used to identify unique experiments
DEDUP_KEY_COLUMNS = [
    "material_type",
    "milling_speed",
    "milling_time",
    "ball_to_powder_ratio",
    "youngs_modulus",
    "density",
]

# Columns used for averaging if duplicates are found
# We prioritize target metrics and process duration
AGGREGATION_RULES = {
    "d10": "mean",
    "d50": "mean",
    "d90": "mean",
    "process_duration": "mean",
    "experiment_id": "first",  # Keep the first encountered ID
    "source": "first",
}

def calculate_row_hash(df: pd.DataFrame, key_columns: List[str]) -> pd.Series:
    """
    Calculate a hash for each row based on key columns to identify duplicates.
    Handles NaN values by replacing them with a sentinel string.
    """
    if not all(col in df.columns for col in key_columns):
        raise DataIngestionError(
            f"Missing required columns for deduplication. "
            f"Expected: {key_columns}, Found: {list(df.columns)}"
        )

    # Create a string representation of the key columns for hashing
    # Replace NaN with a specific string to ensure consistent hashing
    hash_input = df[key_columns].fillna("__NaN__").astype(str)
    
    # Combine columns into a single string per row
    combined = hash_input.apply(lambda row: "|".join(row), axis=1)
    
    # Calculate MD5 hash
    return combined.apply(lambda x: hashlib.md5(x.encode("utf-8")).hexdigest())

def merge_datasets(
    dataframes: List[pd.DataFrame], 
    output_path: Optional[Path] = None
) -> pd.DataFrame:
    """
    Merge multiple DataFrames from different sources (Materials Project, NIST, arXiv),
    perform deduplication based on experimental parameters, and handle conflicting
    PSD measurements.

    Args:
        dataframes: List of DataFrames from different ingestion sources.
        output_path: Optional path to write the merged parquet file.

    Returns:
        Merged and deduplicated DataFrame.

    Raises:
        DataIngestionError: If input list is empty or contains invalid types.
        SchemaValidationError: If required columns are missing in any DataFrame.
    """
    if not dataframes:
        raise DataIngestionError("No dataframes provided for merging.")

    # Validate inputs
    for i, df in enumerate(dataframes):
        if not isinstance(df, pd.DataFrame):
            raise DataIngestionError(f"Item at index {i} is not a DataFrame.")
        if df.empty:
            logger.warning(f"Empty DataFrame provided at index {i}, skipping.")

    # Filter out empty dataframes
    valid_dfs = [df for df in dataframes if not df.empty]

    if not valid_dfs:
        raise DataIngestionError("All provided DataFrames were empty.")

    # Check for required columns in all dataframes
    required_cols = set(DEDUP_KEY_COLUMNS) | {"d10", "d50", "d90"}
    for i, df in enumerate(valid_dfs):
        missing = required_cols - set(df.columns)
        if missing:
            raise DataIngestionError(
                f"DataFrame at index {i} missing required columns: {missing}"
            )

    # Concatenate all dataframes
    logger.info(f"Merging {len(valid_dfs)} datasets...")
    combined_df = pd.concat(valid_dfs, ignore_index=True)
    logger.info(f"Combined dataset size: {len(combined_df)} rows")

    # Identify duplicates
    combined_df["_dedup_hash"] = calculate_row_hash(combined_df, DEDUP_KEY_COLUMNS)
    
    # Count duplicates to log
    dup_counts = combined_df["_dedup_hash"].value_counts()
    num_duplicates = (dup_counts > 1).sum()
    total_dup_rows = dup_counts[dup_counts > 1].sum()
    
    logger.info(f"Found {num_duplicates} groups of duplicates ({total_dup_rows} total rows).")

    if num_duplicates > 0:
        logger.info("Deduplicating based on experimental parameters...")
        
        # Group by hash and aggregate
        # We use the aggregation rules defined above
        agg_dict = {col: rule for col, rule in AGGREGATION_RULES.items() if col in combined_df.columns}
        # Ensure all non-key columns are handled (drop or mean)
        for col in combined_df.columns:
            if col not in agg_dict and col != "_dedup_hash":
                # If it's a numeric column, take mean; otherwise, take first
                if pd.api.types.is_numeric_dtype(combined_df[col]):
                    agg_dict[col] = "mean"
                else:
                    agg_dict[col] = "first"

        deduplicated_df = combined_df.groupby("_dedup_hash").agg(agg_dict).reset_index(drop=True)
        
        # Drop the temporary hash column
        if "_dedup_hash" in deduplicated_df.columns:
            deduplicated_df.drop(columns=["_dedup_hash"], inplace=True)
        
        logger.info(f"Deduplicated dataset size: {len(deduplicated_df)} rows")
    else:
        deduplicated_df = combined_df.drop(columns=["_dedup_hash"])
        logger.info("No duplicates found.")

    # Log conflicting measurements (where std dev of targets is high)
    # This is a heuristic to flag potential data quality issues
    if num_duplicates > 0:
        # Re-calculate on the original grouped data to find conflicts
        # We need to look at the original combined_df before dropping hash
        combined_df["_dedup_hash"] = calculate_row_hash(combined_df, DEDUP_KEY_COLUMNS)
        conflict_report = []
        
        for hash_val, group in combined_df.groupby("_dedup_hash"):
            if len(group) > 1:
                # Check variance in target variables
                for target in ["d10", "d50", "d90"]:
                    if target in group.columns:
                        std_val = group[target].std()
                        mean_val = group[target].mean()
                        if mean_val > 0 and (std_val / mean_val) > 0.2: # 20% variance threshold
                            conflict_report.append({
                                "key_hash": hash_val,
                                "target": target,
                                "mean": mean_val,
                                "std": std_val,
                                "variance_pct": (std_val / mean_val) * 100,
                                "source_count": len(group["source"].unique())
                            })
        
        if conflict_report:
            logger.warning(f"Found {len(conflict_report)} potential conflicts with >20% variance in target measurements.")
            # Log first few conflicts
            for i, conflict in enumerate(conflict_report[:3]):
                logger.warning(f"Conflict {i+1}: {conflict['target']} variance {conflict['variance_pct']:.1f}%")

    # Final validation: ensure no NaN in critical target columns
    critical_targets = ["d10", "d50", "d90"]
    nan_counts = deduplicated_df[critical_targets].isna().sum()
    if nan_counts.any():
        logger.error(f"Found NaN values in critical target columns after merge: {nan_counts.to_dict()}")
        # We do not raise an error here to allow the pipeline to continue to the size check,
        # but we log it heavily. The size check or schema validation downstream might catch it.

    # Write output if path provided
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        deduplicated_df.to_parquet(output_path, index=False)
        logger.info(f"Merged dataset written to {output_path}")

    return deduplicated_df

def run_merge_pipeline(
    raw_data_paths: List[Path],
    output_path: Path,
    source_labels: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Orchestrate the loading, merging, and deduplication of raw data files.

    Args:
        raw_data_paths: List of paths to parquet/CSV files from ingestion steps.
        output_path: Path to write the final merged dataset.
        source_labels: Optional list of labels to tag the source of each file.

    Returns:
        The merged DataFrame.
    """
    dataframes = []
    
    for i, path in enumerate(raw_data_paths):
        if not path.exists():
            raise DataIngestionError(f"Input file not found: {path}")
        
        logger.info(f"Loading data from {path}...")
        if path.suffix == ".parquet":
            df = pd.read_parquet(path)
        elif path.suffix == ".csv":
            df = pd.read_csv(path)
        else:
            raise DataIngestionError(f"Unsupported file format: {path.suffix}")
        
        # Tag source if labels provided
        if source_labels and i < len(source_labels):
            df["source"] = source_labels[i]
        elif "source" not in df.columns:
            df["source"] = f"unknown_source_{i}"
        
        dataframes.append(df)

    return merge_datasets(dataframes, output_path)
