"""
Merge and Deduplicate logic for ball milling data ingestion.
Implements T015a (Merge) and T015b (Validate Traceability).
"""
import hashlib
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd

from src.utils.logger import get_module_logger
from src.utils.exceptions import InsufficientDataError

logger = get_module_logger(__name__)

# Required traceability fields per spec
TRACEABILITY_FIELDS = ["source_name", "source_id"]

def calculate_row_hash(row: pd.Series) -> str:
    """
    Calculate a deterministic hash for a row to detect duplicates.
    Uses a subset of columns that define a unique experiment.
    """
    # Define a subset of columns that uniquely identify an experiment
    # excluding the target variables which might vary slightly due to measurement error
    # but for strict deduplication we use the full row string representation for now.
    # A more robust approach might use specific feature columns.
    row_str = str(row.to_dict())
    return hashlib.sha256(row_str.encode("utf-8")).hexdigest()

def merge_datasets(
    data_sources: Dict[str, pd.DataFrame], output_path: str
) -> Tuple[pd.DataFrame, int]:
    """
    Merge multiple data sources into a single DataFrame.

    Args:
        data_sources: Dictionary mapping source name to DataFrame.
        output_path: Path to save the merged parquet file.

    Returns:
        Tuple of (merged DataFrame, total row count).
    """
    logger.info(f"Merging {len(data_sources)} data sources...")

    if not data_sources:
        logger.warning("No data sources provided for merge.")
        # Create an empty DataFrame with expected schema if needed, or return empty
        # For now, return empty to let downstream handle the size gate.
        merged_df = pd.DataFrame()
        return merged_df, 0

    dfs = []
    for source_name, df in data_sources.items():
        if df is None or df.empty:
            logger.warning(f"Source '{source_name}' is empty or None. Skipping.")
            continue

        # Ensure traceability columns are present and set
        # T015a requires: Validate that every row has non-null source_name and source_id.
        # We enforce this here by filling or flagging.
        # However, the task says: "If any row lacks these, flag it... but NOT dropped... unless lacks valid data".
        # For the MERGE output, we keep them. The VALIDATION task (T015b) will check strictly.
        # We ensure the columns exist.
        df = df.copy()
        if "source_name" not in df.columns:
            df["source_name"] = source_name
        if "source_id" not in df.columns:
            # If source_id is missing, we cannot invent one. We leave it as NaN.
            # The traceability validation will flag these.
            df["source_id"] = None

        dfs.append(df)
        logger.info(f"Appended {len(df)} rows from {source_name}.")

    if not dfs:
        logger.warning("No valid data rows found in any source.")
        merged_df = pd.DataFrame()
        return merged_df, 0

    merged_df = pd.concat(dfs, ignore_index=True)
    logger.info(f"Merged dataset size: {len(merged_df)} rows.")

    # Save to parquet
    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)
    merged_df.to_parquet(output_path, index=False)
    logger.info(f"Merged dataset saved to {output_path}")

    return merged_df, len(merged_df)

def validate_traceability(df: pd.DataFrame) -> Tuple[int, List[Dict]]:
    """
    Validate traceability of merged data (T015b).
    Ensures all rows have non-null 'source_name' and 'source_id'.

    Args:
        df: The merged DataFrame.

    Returns:
        Tuple of (count of valid rows, list of flagged row info).
    """
    if df.empty:
        logger.warning("DataFrame is empty. Traceability validation skipped.")
        return 0, []

    flagged_rows = []
    valid_count = 0

    # Check for nulls in traceability columns
    # Spec: "If any row lacks these, flag it for manual review and log"
    # We do NOT drop them here, just count valid ones and report flags.
    for idx, row in df.iterrows():
        is_valid = True
        issues = []

        if pd.isna(row.get("source_name")) or row.get("source_name") == "":
            is_valid = False
            issues.append("missing source_name")

        if pd.isna(row.get("source_id")) or row.get("source_id") == "":
            is_valid = False
            issues.append("missing source_id")

        if is_valid:
            valid_count += 1
        else:
            flagged_rows.append({
                "index": int(idx),
                "issues": issues,
                "source_name": row.get("source_name"),
                "source_id": row.get("source_id"),
                # Include a hash of the row for manual review reference if needed
                "row_hash": calculate_row_hash(row)
            })
            logger.warning(
                f"Row flagged: missing traceability metadata at index {idx}. "
                f"Issues: {', '.join(issues)}"
            )

    if flagged_rows:
        logger.warning(
            f"Traceability validation found {len(flagged_rows)} rows with missing metadata. "
            "These rows are flagged for manual review but included in the dataset."
        )
    else:
        logger.info("Traceability validation passed: all rows have source_name and source_id.")

    return valid_count, flagged_rows

def process_flagged_entries(
    flagged_rows: List[Dict], flagged_output_path: str
) -> None:
    """
    Save flagged rows to a JSON file for manual review.
    """
    if not flagged_rows:
        logger.info("No flagged entries to save.")
        # Create an empty file to ensure the path exists if expected by downstream
        Path(flagged_output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(flagged_output_path, "w") as f:
            json.dump([], f)
        return

    Path(flagged_output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(flagged_output_path, "w") as f:
        json.dump(flagged_rows, f, indent=2)
    logger.info(f"Flagged entries saved to {flagged_output_path}")

def run_merge_pipeline(
    data_sources: Dict[str, pd.DataFrame],
    merge_output_path: str = "data/raw/merged_dataset.parquet",
    flagged_output_path: str = "data/flagged_psd.json",
) -> Tuple[pd.DataFrame, int]:
    """
    Orchestrates the merge and traceability validation.

    Returns:
        Tuple of (merged DataFrame, count of valid traceable rows).
    """
    # 1. Merge
    merged_df, total_rows = merge_datasets(data_sources, merge_output_path)

    if merged_df.empty:
        return merged_df, 0

    # 2. Validate Traceability (T015b)
    valid_count, flagged_rows = validate_traceability(merged_df)

    # 3. Save flagged entries
    process_flagged_entries(flagged_rows, flagged_output_path)

    # Log the size warning if < 150 (T015a requirement)
    if valid_count < 150:
        logger.critical(
            f"Merged dataset size < 150 experiments (minimum viable) per spec SC-004. "
            f"Valid traceable rows: {valid_count}, Total rows: {total_rows}."
        )
    else:
        logger.info(f"Merged dataset size OK: {valid_count} valid traceable rows.")

    return merged_df, valid_count

def save_to_json(df: pd.DataFrame, path: str) -> None:
    """Helper to save dataframe to JSON for intermediate steps if needed."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    df.to_json(path, orient="records", indent=2)
    logger.info(f"Saved dataframe to {path}")

# Main entry point for standalone execution (e.g. for testing or specific pipeline steps)
def main():
    """
    Example main function to demonstrate usage.
    In the real pipeline, this is called by src/cli/ingest.py.
    """
    logger.info("Running merge pipeline...")
    # This would be populated by the ingestion steps (T012, T013, T013b, T014c)
    # For this task, we assume data_sources is provided or loaded.
    # Since we cannot run the full ingestion here without real data,
    # we demonstrate the function signature and logic structure.
    # In a real run, data_sources would be loaded from the raw JSON files.

    # Example of loading data if files exist (for a full run)
    # data_sources = {}
    # mp_path = "data/raw/materials_project_raw.json"
    # if Path(mp_path).exists():
    #     data_sources["Materials Project"] = pd.read_json(mp_path)
    # ... similar for others

    # For now, just log that the function is ready.
    logger.info("Merge pipeline logic implemented. Ready for ingestion data.")

if __name__ == "__main__":
    main()
