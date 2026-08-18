import hashlib
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pandas as pd

from src.exceptions import InsufficientDataError
from src.utils.logger import get_module_logger
from src.utils.seed import get_seed

logger = get_module_logger(__name__)

def calculate_row_hash(row: pd.Series) -> str:
    """
    Calculate a deterministic hash for a row based on its content.
    Used to identify duplicates across sources.
    """
    # Convert row to string, handling NaNs explicitly
    row_str = row.astype(str).sort_index().to_json()
    return hashlib.sha256(row_str.encode('utf-8')).hexdigest()

def merge_datasets(
    materials_project_df: Optional[pd.DataFrame],
    nist_df: Optional[pd.DataFrame],
    arxiv_df: Optional[pd.DataFrame],
    output_path: Path
) -> pd.DataFrame:
    """
    Merge datasets from multiple sources, deduplicate based on experiment_id,
    and save the result.

    Args:
        materials_project_df: DataFrame from Materials Project
        nist_df: DataFrame from NIST
        arxiv_df: DataFrame from arXiv
        output_path: Path to save the merged dataset

    Returns:
        Merged and deduplicated DataFrame

    Raises:
        InsufficientDataError: If the merged dataset has fewer than 150 rows
    """
    dfs = []
    source_counts = {}

    # Collect non-empty DataFrames
    if materials_project_df is not None and not materials_project_df.empty:
        dfs.append(materials_project_df)
        source_counts['materials_project'] = len(materials_project_df)
        logger.info(f"Added {len(materials_project_df)} rows from Materials Project")

    if nist_df is not None and not nist_df.empty:
        dfs.append(nist_df)
        source_counts['nist'] = len(nist_df)
        logger.info(f"Added {len(nist_df)} rows from NIST")

    if arxiv_df is not None and not arxiv_df.empty:
        dfs.append(arxiv_df)
        source_counts['arxiv'] = len(arxiv_df)
        logger.info(f"Added {len(arxiv_df)} rows from arXiv")

    if not dfs:
        logger.error("No data sources provided. Cannot merge.")
        raise InsufficientDataError("No data sources provided. Cannot merge.")

    # Concatenate all DataFrames
    merged_df = pd.concat(dfs, ignore_index=True)
    logger.info(f"Total rows before deduplication: {len(merged_df)}")

    # Ensure experiment_id column exists
    if 'experiment_id' not in merged_df.columns:
        # Generate unique IDs if not present
        seed = get_seed()
        merged_df['experiment_id'] = [
            f"exp_{i:06d}" for i in range(len(merged_df))
        ]
        logger.warning("Generated experiment_id column as it was missing.")

    # Deduplicate based on experiment_id
    initial_count = len(merged_df)
    merged_df = merged_df.drop_duplicates(subset=['experiment_id'], keep='first')
    duplicates_removed = initial_count - len(merged_df)

    if duplicates_removed > 0:
        logger.info(f"Removed {duplicates_removed} duplicate entries based on experiment_id")

    # Check minimum viable dataset size
    min_viable_size = 150
    if len(merged_df) < min_viable_size:
        logger.error(f"Processed dataset size ({len(merged_df)}) < {min_viable_size} experiments (minimum viable) per spec SC-004")
        raise InsufficientDataError(
            f"Processed dataset size < 150 experiments (minimum viable) per spec SC-004"
        )

    # Save to parquet
    output_path.parent.mkdir(parents=True, exist_ok=True)
    merged_df.to_parquet(output_path, index=False)
    logger.info(f"Saved merged dataset to {output_path} with {len(merged_df)} rows")

    return merged_df

def validate_traceability(merged_df: pd.DataFrame) -> Dict[str, int]:
    """
    Validate that all rows have traceable source information.

    Args:
        merged_df: The merged DataFrame

    Returns:
        Dictionary with counts per source
    """
    if 'source' not in merged_df.columns:
        logger.warning("No 'source' column found in merged dataset")
        return {}

    source_counts = merged_df['source'].value_counts().to_dict()
    logger.info(f"Traceability validation complete. Sources: {source_counts}")
    return source_counts

def process_flagged_entries(merged_df: pd.DataFrame, flagged_log_path: Path) -> pd.DataFrame:
    """
    Process flagged entries from the merge.

    Args:
        merged_df: The merged DataFrame
        flagged_log_path: Path to the flagged entries log

    Returns:
        DataFrame with flagged entries marked
    """
    if not flagged_log_path.exists():
        logger.info("No flagged entries log found. Skipping flagged entry processing.")
        return merged_df

    try:
        with open(flagged_log_path, 'r') as f:
            flagged_entries = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"Could not load flagged entries log: {e}")
        return merged_df

    flagged_ids = set(entry.get('experiment_id') for entry in flagged_entries if entry.get('experiment_id'))
    merged_df['needs_manual_review'] = merged_df['experiment_id'].isin(flagged_ids)

    review_count = merged_df['needs_manual_review'].sum()
    logger.info(f"Marked {review_count} entries for manual review")

    return merged_df

def run_merge_pipeline(
    materials_project_path: Optional[Path] = None,
    nist_path: Optional[Path] = None,
    arxiv_path: Optional[Path] = None,
    flagged_log_path: Optional[Path] = None,
    output_path: Optional[Path] = None
) -> pd.DataFrame:
    """
    Run the complete merge pipeline: load, merge, deduplicate, validate, and save.

    Args:
        materials_project_path: Path to Materials Project data JSON
        nist_path: Path to NIST data JSON
        arxiv_path: Path to arXiv data JSON
        flagged_log_path: Path to flagged entries log
        output_path: Path to save the merged dataset

    Returns:
        Merged and processed DataFrame
    """
    if output_path is None:
        output_path = Path("data/raw/merged_dataset.parquet")

    # Load data from sources
    materials_project_df = None
    nist_df = None
    arxiv_df = None

    if materials_project_path and materials_project_path.exists():
        try:
            materials_project_df = pd.read_json(materials_project_path)
            materials_project_df['source'] = 'materials_project'
        except Exception as e:
            logger.warning(f"Failed to load Materials Project data: {e}")

    if nist_path and nist_path.exists():
        try:
            nist_df = pd.read_json(nist_path)
            nist_df['source'] = 'nist'
        except Exception as e:
            logger.warning(f"Failed to load NIST data: {e}")

    if arxiv_path and arxiv_path.exists():
        try:
            arxiv_df = pd.read_json(arxiv_path)
            arxiv_df['source'] = 'arxiv'
        except Exception as e:
            logger.warning(f"Failed to load arXiv data: {e}")

    # Merge datasets
    merged_df = merge_datasets(
        materials_project_df,
        nist_df,
        arxiv_df,
        output_path
    )

    # Validate traceability
    validate_traceability(merged_df)

    # Process flagged entries if log exists
    if flagged_log_path:
        merged_df = process_flagged_entries(merged_df, flagged_log_path)

    return merged_df

def save_to_json(df: pd.DataFrame, path: Path) -> None:
    """Save DataFrame to JSON."""
    df.to_json(path, orient='records', indent=2)
    logger.info(f"Saved DataFrame to {path}")

def main():
    """Main entry point for the merge pipeline."""
    logger.info("Starting merge pipeline")

    # Default paths
    materials_project_path = Path("data/raw/materials_project_data.json")
    nist_path = Path("data/raw/nist_data.json")
    arxiv_path = Path("data/raw/arxiv_data.json")
    flagged_log_path = Path("data/flagged_psd.log")
    output_path = Path("data/raw/merged_dataset.parquet")

    try:
        run_merge_pipeline(
            materials_project_path=materials_project_path,
            nist_path=nist_path,
            arxiv_path=arxiv_path,
            flagged_log_path=flagged_log_path,
            output_path=output_path
        )
        logger.info("Merge pipeline completed successfully")
    except InsufficientDataError as e:
        logger.error(str(e))
        raise
    except Exception as e:
        logger.error(f"Merge pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()