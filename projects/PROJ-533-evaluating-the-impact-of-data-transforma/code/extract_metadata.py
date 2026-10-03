"""
Task T017: Implement metadata extraction for retained datasets.

This script loads the filtered datasets (from data/filtered/), computes global
statistics (sample size, skewness, kurtosis) for continuous variables, and writes
the metadata to data/datasets.csv.

CRITICAL: Must run AFTER T016 (Filtering) and T014 (Checksums).
Must load full dataset (or a representative sample via streaming) to compute
global statistics required for downstream simulation (T024a).
"""
import os
import sys
import csv
import logging
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from code.utils.logging_config import setup_pipeline_logger
from code.utils.schema_definitions import get_datasets_headers
from code.utils.checkpointing import load_state, save_state

# Configure logger
logger = setup_pipeline_logger("extract_metadata")

FILTERED_DIR = project_root / "data" / "filtered"
DATASETS_CSV = project_root / "data" / "datasets.csv"
CHECKSUMS_CSV = project_root / "data" / "checksums.csv"
FILTER_RESULTS_CSV = project_root / "data" / "filter_results.csv"

def load_filtered_dataset(filepath: Path) -> pd.DataFrame:
    """Load a filtered dataset from CSV or parquet."""
    if not filepath.exists():
        raise FileNotFoundError(f"Filtered dataset not found: {filepath}")

    suffix = filepath.suffix.lower()
    if suffix == '.csv':
        return pd.read_csv(filepath)
    elif suffix in ['.parquet', '.pq']:
        return pd.read_parquet(filepath)
    else:
        # Try CSV as fallback
        try:
            return pd.read_csv(filepath)
        except Exception:
            raise ValueError(f"Unsupported file format: {suffix}")

def compute_global_stats(df: pd.DataFrame, continuous_cols: List[str]) -> Dict[str, Any]:
    """
    Compute global statistics (skewness, kurtosis) for continuous variables.
    Uses the full dataset to ensure accuracy for downstream simulation.
    """
    stats = {}
    for col in continuous_cols:
        if col in df.columns and df[col].notna().sum() > 0:
            series = df[col].dropna()
            if len(series) > 2:
                stats[col] = {
                    'skewness': float(series.skew()),
                    'kurtosis': float(series.kurtosis())
                }
            else:
                stats[col] = {'skewness': None, 'kurtosis': None}
        else:
            stats[col] = {'skewness': None, 'kurtosis': None}
    return stats

def identify_continuous_columns(df: pd.DataFrame) -> List[str]:
    """Identify continuous (numeric) columns in the dataframe."""
    return df.select_dtypes(include=[np.number]).columns.tolist()

def get_checksum_for_dataset(dataset_id: str) -> Optional[str]:
    """Retrieve the checksum for a dataset from the checksums.csv file."""
    if not CHECKSUMS_CSV.exists():
        logger.warning(f"Checksums file not found: {CHECKSUMS_CSV}")
        return None

    with open(CHECKSUMS_CSV, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('dataset_id') == dataset_id:
                return row.get('checksum')
    return None

def get_filter_result(dataset_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve the filter result for a dataset from filter_results.csv."""
    if not FILTER_RESULTS_CSV.exists():
        logger.warning(f"Filter results file not found: {FILTER_RESULTS_CSV}")
        return None

    with open(FILTER_RESULTS_CSV, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('dataset_id') == dataset_id:
                return row
    return None

def extract_metadata_for_dataset(dataset_id: str, filepath: Path) -> Optional[Dict[str, Any]]:
    """Extract metadata for a single dataset."""
    try:
        logger.info(f"Processing dataset: {dataset_id}")
        df = load_filtered_dataset(filepath)

        # Identify continuous variables
        continuous_cols = identify_continuous_columns(df)
        if not continuous_cols:
            logger.warning(f"No continuous columns found in {dataset_id}")
            return None

        # Compute global statistics (skewness, kurtosis)
        global_stats = compute_global_stats(df, continuous_cols)

        # Get checksum
        checksum = get_checksum_for_dataset(dataset_id)

        # Get filter result (to confirm it passed)
        filter_result = get_filter_result(dataset_id)
        if filter_result and filter_result.get('included', '').lower() != 'true':
            logger.warning(f"Dataset {dataset_id} was excluded during filtering, skipping metadata extraction")
            return None

        # Construct metadata record
        metadata = {
            'dataset_id': dataset_id,
            'source_url': filter_result.get('source_url', '') if filter_result else '',
            'sample_size': int(len(df)),
            'continuous_variables': ','.join(continuous_cols),
            'group_labels': '',  # Will be populated if group labels are detected
            'skewness_stats': json.dumps(global_stats),
            'kurtosis_stats': json.dumps(global_stats),
            'checksum': checksum or '',
            'included': 'true'
        }

        return metadata

    except Exception as e:
        logger.error(f"Failed to extract metadata for {dataset_id}: {e}", exc_info=True)
        return None

def write_metadata_csv(metadata_list: List[Dict[str, Any]]):
    """Write metadata to datasets.csv."""
    if not metadata_list:
        logger.warning("No metadata to write")
        return

    headers = get_datasets_headers()
    # Ensure headers match the expected schema
    expected_headers = ['dataset_id', 'source_url', 'sample_size', 'continuous_variables', 
                      'group_labels', 'skewness_stats', 'kurtosis_stats', 'checksum', 'included']
    
    # Write to CSV
    with open(DATASETS_CSV, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=expected_headers)
        writer.writeheader()
        for metadata in metadata_list:
            # Ensure all expected keys are present
            row = {h: metadata.get(h, '') for h in expected_headers}
            writer.writerow(row)

    logger.info(f"Written {len(metadata_list)} metadata records to {DATASETS_CSV}")

def main():
    """Main entry point for metadata extraction."""
    logger.info("Starting metadata extraction (T017)")

    # Verify prerequisites
    if not FILTERED_DIR.exists():
        logger.error(f"Filtered directory not found: {FILTERED_DIR}")
        sys.exit(1)

    if not CHECKSUMS_CSV.exists():
        logger.error(f"Checksums file not found: {CHECKSUMS_CSV}. Run T014 first.")
        sys.exit(1)

    if not FILTER_RESULTS_CSV.exists():
        logger.error(f"Filter results file not found: {FILTER_RESULTS_CSV}. Run T016 first.")
        sys.exit(1)

    # Get list of filtered dataset files
    dataset_files = list(FILTERED_DIR.glob("*"))
    if not dataset_files:
        logger.warning("No filtered dataset files found")
        sys.exit(0)

    metadata_list = []
    success_count = 0
    failure_count = 0

    for filepath in dataset_files:
        if filepath.is_file():
            # Extract dataset_id from filename (assuming format: dataset_id.csv or dataset_id.parquet)
            dataset_id = filepath.stem
            
            metadata = extract_metadata_for_dataset(dataset_id, filepath)
            if metadata:
                metadata_list.append(metadata)
                success_count += 1
            else:
                failure_count += 1

    # Write results
    write_metadata_csv(metadata_list)

    # Log summary
    logger.info(f"Metadata extraction complete: {success_count} successful, {failure_count} failed")

    # Save checkpoint
    save_state(
        run_id="t017_metadata_extraction",
        step="complete",
        data={
            "success_count": success_count,
            "failure_count": failure_count,
            "output_file": str(DATASETS_CSV)
        }
    )

    logger.info("T017 completed successfully")

if __name__ == "__main__":
    main()
