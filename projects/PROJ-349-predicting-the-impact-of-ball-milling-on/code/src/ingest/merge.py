"""
Merge and deduplicate datasets from multiple sources.
Implements strict 'Fail Loudly' rule for real sources and fallback logic.
"""
import hashlib
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd

from src.exceptions import DataIngestionError, InsufficientDataError
from src.ingest.fallback_aggregator import load_fallback_data, append_fallback_if_needed

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def calculate_row_hash(row: pd.Series) -> str:
    """Calculate a unique hash for a row to detect duplicates."""
    # Create a string representation of the row's values
    # Ensure consistent ordering and formatting
    values = [str(v) if pd.notna(v) else "" for v in row]
    content = "|".join(values)
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def merge_datasets(dfs: List[pd.DataFrame], source_names: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Merge multiple DataFrames and remove duplicates based on a calculated row hash.

    Args:
        dfs: List of DataFrames to merge.
        source_names: Optional list of source names for logging.

    Returns:
        Merged DataFrame with duplicates removed.
    """
    if not dfs:
        logger.warning("No DataFrames provided for merging.")
        return pd.DataFrame()

    # Filter out empty DataFrames
    non_empty_dfs = [df for df in dfs if not df.empty]

    if not non_empty_dfs:
        logger.warning("All provided DataFrames are empty.")
        return pd.DataFrame()

    # Concatenate all non-empty DataFrames
    if len(non_empty_dfs) == 1:
        merged = non_empty_dfs[0].copy()
    else:
        merged = pd.concat(non_empty_dfs, ignore_index=True)

    if merged.empty:
        logger.warning("Merged result is empty.")
        return merged

    # Calculate row hashes
    logger.info(f"Calculating row hashes for {len(merged)} rows...")
    merged['_row_hash'] = merged.apply(calculate_row_hash, axis=1)

    # Drop duplicates based on hash
    initial_count = len(merged)
    merged = merged.drop_duplicates(subset=['_row_hash'])
    final_count = len(merged)
    duplicates_removed = initial_count - final_count

    if duplicates_removed > 0:
        logger.info(f"Removed {duplicates_removed} duplicate rows.")
    else:
        logger.info("No duplicate rows found.")

    # Drop the temporary hash column
    merged = merged.drop(columns=['_row_hash'])

    return merged

def run_merge_pipeline(
    materials_project_df: Optional[pd.DataFrame] = None,
    nist_df: Optional[pd.DataFrame] = None,
    arxiv_df: Optional[pd.DataFrame] = None,
    output_path: str = "data/processed/merged_dataset.csv",
    fallback_threshold: int = 150
) -> pd.DataFrame:
    """
    Orchestrate the merging of data from various sources with strict fallback logic.

    This function enforces the 'Fail Loudly' rule:
    - If a primary source (T012, T013, T013b) fails or returns 0 rows, it logs a warning and skips.
    - If the total count from primary sources is < 150, it attempts to load verified fallback data (T043).
    - It does NOT generate synthetic data.

    Args:
        materials_project_df: DataFrame from Materials Project (T012).
        nist_df: DataFrame from NIST (T013).
        arxiv_df: DataFrame from arXiv (T013b).
        output_path: Path to save the merged dataset.
        fallback_threshold: Minimum row count required to skip fallback.

    Returns:
        The final merged DataFrame.
    """
    sources = []
    source_names = []
    counts = {}

    # Process Materials Project
    if materials_project_df is not None and not materials_project_df.empty:
        sources.append(materials_project_df)
        source_names.append("Materials Project")
        counts["Materials Project"] = len(materials_project_df)
        logger.info(f"Loaded {len(materials_project_df)} rows from Materials Project.")
    else:
        logger.warning("Source skipped: Materials Project (0 rows or error)")
        counts["Materials Project"] = 0

    # Process NIST
    if nist_df is not None and not nist_df.empty:
        sources.append(nist_df)
        source_names.append("NIST")
        counts["NIST"] = len(nist_df)
        logger.info(f"Loaded {len(nist_df)} rows from NIST.")
    else:
        logger.warning("Source skipped: NIST (0 rows or error)")
        counts["NIST"] = 0

    # Process arXiv
    if arxiv_df is not None and not arxiv_df.empty:
        sources.append(arxiv_df)
        source_names.append("arXiv")
        counts["arXiv"] = len(arxiv_df)
        logger.info(f"Loaded {len(arxiv_df)} rows from arXiv.")
    else:
        logger.warning("Source skipped: arXiv (0 rows or error)")
        counts["arXiv"] = 0

    # Merge primary sources
    merged_df = merge_datasets(sources, source_names)
    total_count = len(merged_df)

    logger.info(f"Total rows from primary sources: {total_count}")

    # Check if fallback is needed
    if total_count < fallback_threshold:
        logger.warning(f"Total count ({total_count}) is below threshold ({fallback_threshold}). Attempting to load verified fallback data.")
        try:
            fallback_df = load_fallback_data()
            if fallback_df is not None and not fallback_df.empty:
                logger.info(f"Loaded {len(fallback_df)} rows from verified fallback.")
                # Merge with existing data
                final_df = merge_datasets([merged_df, fallback_df], source_names + ["UCI Fallback"])
                final_count = len(final_df)
                logger.info(f"Total rows after fallback: {final_count}")
                
                # Ensure output directory exists
                Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                final_df.to_csv(output_path, index=False)
                logger.info(f"Merged dataset saved to {output_path}")
                
                return final_df
            else:
                logger.warning("Fallback data source returned empty or invalid data.")
                # Proceed with partial data, but log critical warning
                logger.critical("Insufficient real data available. Pipeline may halt later at size gate.")
        except Exception as e:
            logger.error(f"Failed to load fallback data: {e}")
            # Proceed with partial data, but log critical warning
            logger.critical("Insufficient real data available. Pipeline may halt later at size gate.")
    
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    merged_df.to_csv(output_path, index=False)
    logger.info(f"Merged dataset saved to {output_path}")

    return merged_df
