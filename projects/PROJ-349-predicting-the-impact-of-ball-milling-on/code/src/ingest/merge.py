"""
Data merger and deduplication logic for ball milling dataset.
Handles merging of data from multiple sources and deduplication of conflicting PSD measurements.
"""

import hashlib
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from src.utils.logger import get_module_logger
from src.utils.exceptions import DataIngestionError
from src.ingest.ocr_fallback import extract_psd_from_image
from src.config.settings import load_config

logger = get_module_logger(__name__)


def calculate_row_hash(row: pd.Series) -> str:
    """
    Calculate a deterministic hash for a row based on its content.
    Used for identifying duplicate entries across sources.

    Args:
        row: A pandas Series representing a single row.

    Returns:
        A hexadecimal string hash of the row's content.
    """
    # Create a string representation of the row's values
    # Sort keys to ensure deterministic hashing
    row_dict = row.to_dict()
    sorted_items = sorted(row_dict.items())
    row_str = str(sorted_items)
    return hashlib.sha256(row_str.encode('utf-8')).hexdigest()


def merge_datasets(dataframes: List[pd.DataFrame]) -> pd.DataFrame:
    """
    Merge multiple dataframes and remove duplicate rows based on a hash.

    Args:
        dataframes: List of pandas DataFrames to merge.

    Returns:
        A merged DataFrame with duplicates removed.
    """
    if not dataframes:
        logger.warning("No dataframes provided to merge.")
        return pd.DataFrame()

    # Filter out empty dataframes
    valid_dfs = [df for df in dataframes if not df.empty]

    if not valid_dfs:
        logger.warning("All provided dataframes were empty.")
        return pd.DataFrame()

    logger.info(f"Merging {len(valid_dfs)} dataframes.")

    # Concatenate all dataframes
    merged_df = pd.concat(valid_dfs, ignore_index=True)
    logger.info(f"Pre-deduplication row count: {len(merged_df)}")

    # Add a hash column for deduplication
    merged_df['_row_hash'] = merged_df.apply(calculate_row_hash, axis=1)

    # Remove duplicates based on the hash
    merged_df = merged_df.drop_duplicates(subset=['_row_hash'])

    # Drop the temporary hash column
    merged_df = merged_df.drop(columns=['_row_hash'])

    logger.info(f"Post-deduplication row count: {len(merged_df)}")

    return merged_df


def validate_traceability(df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
    """
    Validate that every row has non-null source_name and source_id.
    Filter out rows that lack these traceability fields.

    Args:
        df: The merged DataFrame.

    Returns:
        A tuple of (filtered DataFrame, count of filtered rows).
    """
    if df.empty:
        logger.warning("DataFrame is empty, skipping traceability validation.")
        return df, 0

    required_cols = ['source_name', 'source_id']
    missing_mask = df[required_cols].isnull().any(axis=1)
    count_filtered = missing_mask.sum()

    if count_filtered > 0:
        logger.warning(f"Filtering out {count_filtered} rows with missing traceability metadata.")
        logger.warning("Rows without source_name or source_id are not allowed per spec.")
        df = df[~missing_mask].reset_index(drop=True)

    return df, count_filtered


def process_flagged_entries(df: pd.DataFrame, config: Optional[Dict] = None) -> pd.DataFrame:
    """
    Process entries flagged in data/flagged_psd.json by attempting OCR extraction.

    Args:
        df: The merged DataFrame.
        config: Optional config dictionary. If None, loads from default config.

    Returns:
        The DataFrame with updated PSD values for successfully extracted flagged entries.
    """
    flagged_path = Path("data/flagged_psd.json")
    if not flagged_path.exists():
        logger.info("No flagged entries file found. Skipping OCR fallback.")
        return df

    try:
        with open(flagged_path, 'r') as f:
            flagged_data = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Failed to load flagged entries: {e}")
        return df

    if not flagged_data:
        logger.info("Flagged entries file is empty. Skipping OCR fallback.")
        return df

    if config is None:
        try:
            config = load_config()
        except Exception as e:
            logger.warning(f"Failed to load config for OCR fallback: {e}. Skipping OCR.")
            return df

    ocr_enabled = config.get('ocr_enabled', False)
    if not ocr_enabled:
        logger.info("OCR is disabled in config. Skipping extraction for flagged entries.")
        return df

    updated_rows = []
    for entry in flagged_data:
        entry_id = entry.get('experiment_id')
        image_path = entry.get('image_path')

        if not entry_id or not image_path:
            logger.warning(f"Invalid flagged entry: {entry}. Skipping.")
            continue

        try:
            extracted_data = extract_psd_from_image(image_path, entry_id, config)
            if extracted_data:
                # Update the dataframe if we found a matching row
                mask = (df['experiment_id'] == entry_id)
                if mask.any():
                    for key, value in extracted_data.items():
                        if key in df.columns:
                            df.loc[mask, key] = value
                    logger.info(f"Successfully updated entry {entry_id} with OCR data.")
                else:
                    logger.warning(f"No matching row found for experiment_id {entry_id} in merged dataset.")
        except Exception as e:
            logger.warning(f"Failed to extract PSD from image for {entry_id}: {e}")

    return df


def run_merge_pipeline(
    materials_df: Optional[pd.DataFrame] = None,
    nist_df: Optional[pd.DataFrame] = None,
    arxiv_df: Optional[pd.DataFrame] = None
) -> pd.DataFrame:
    """
    Main pipeline function to merge data from all sources, validate traceability,
    process flagged entries, and save the result.

    Args:
        materials_df: DataFrame from Materials Project ingestion.
        nist_df: DataFrame from NIST ingestion.
        arxiv_df: DataFrame from arXiv ingestion.

    Returns:
        The final merged and validated DataFrame.
    """
    logger.info("Starting merge pipeline.")

    # Collect non-empty dataframes
    dataframes = []
    if materials_df is not None and not materials_df.empty:
        dataframes.append(materials_df)
    if nist_df is not None and not nist_df.empty:
        dataframes.append(nist_df)
    if arxiv_df is not None and not arxiv_df.empty:
        dataframes.append(arxiv_df)

    if not dataframes:
        logger.warning("No data to merge. Returning empty DataFrame.")
        return pd.DataFrame()

    # Merge datasets
    merged_df = merge_datasets(dataframes)

    # Validate traceability
    merged_df, filtered_count = validate_traceability(merged_df)
    logger.info(f"Traceability validation complete. Filtered {filtered_count} rows.")

    # Process flagged entries (OCR fallback)
    merged_df = process_flagged_entries(merged_df)

    # Ensure output directory exists
    output_path = Path("data/raw/merged_dataset.parquet")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save to Parquet
    try:
        table = pa.Table.from_pandas(merged_df)
        pq.write_table(table, output_path)
        logger.info(f"Merged dataset saved to {output_path}")
    except Exception as e:
        logger.error(f"Failed to save merged dataset: {e}")
        raise DataIngestionError(f"Failed to save merged dataset: {e}")

    logger.info(f"Merge pipeline complete. Final row count: {len(merged_df)}")
    return merged_df
