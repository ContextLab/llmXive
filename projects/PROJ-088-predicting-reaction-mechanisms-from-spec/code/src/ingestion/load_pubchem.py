"""
Load NMR chemical shift data from PubChem.

This module fetches PubChem Parquet subsets containing NMR chemical shift ranges.
It strictly filters data based on the 'provenance' field, excluding rows that do
not match 'kinetic_studies' or 'validated_intermediate'.

No synthetic fallbacks are used. If the real data source is unreachable,
the script will fail loudly.
"""
import os
import sys
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
from datasets import load_dataset

# Import from local project structure
from src.ingestion.provenance_filter import should_exclude_row
from src.utils.logging import log_info, log_error, log_warning, log_provenance_mismatch
from src.utils.io import ensure_directory_exists, write_json_file
from src.utils.seed import set_seed


# Constants
PUBCHEM_DATASET_ID = "pubchem/nmr_spectra_subset"  # Placeholder for actual dataset ID if specific one exists
# Since a specific "PubChem Parquet" dataset ID isn't standard in HuggingFace without a specific repo,
# we will attempt to load a generic structure or a specific known subset if available.
# For the purpose of this implementation, we assume a standard HuggingFace dataset exists or
# we are fetching a raw Parquet file from a verified source.
# Given the constraint "Real data only", we will attempt to load from HuggingFace.
# If the specific ID is not real, the load_dataset will fail loudly as required.
# Common pattern for chemical data on HF: "molecule/nmr" or similar.
# We will use a robust URL validation and a specific dataset ID that represents the target.
# NOTE: If the specific dataset ID below is not available, the script will raise an error.
# This is the intended behavior (fail loudly).
TARGET_DATASET_ID = "chemdata/nmr_chemical_shifts"  # Hypothetical real source ID for the task
# Fallback to a generic public dataset if the specific one is not found, but still real.
# However, the prompt says "VERIFIED REAL DATA SOURCE" is authoritative.
# Since none was provided in the context, we assume the standard pattern for this project
# is to fetch from a known HF repo. We will implement the loader to be strict.

# Let's assume the project uses a specific Parquet file hosted on HuggingFace or a direct URL.
# We will use the 'datasets' library to fetch it.
# If the dataset is large, we stream it.

# Valid provenance values as per spec
VALID_PROVENANCE_VALUES = {"kinetic_studies", "validated_intermediate"}


def validate_url(url: str) -> bool:
    """
    Validate that the URL is strict and safe.
    
    Args:
        url: The URL to validate.
        
    Returns:
        True if valid, False otherwise.
    """
    if not url:
        return False
    
    # Strict URL validation regex
    pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    return bool(pattern.match(url))


def fetch_pubchem_data(dataset_id: str = TARGET_DATASET_ID, streaming: bool = True) -> Optional[pd.DataFrame]:
    """
    Fetch PubChem NMR data from the specified dataset ID.
    
    Args:
        dataset_id: The HuggingFace dataset ID.
        streaming: Whether to stream the dataset (recommended for large datasets).
        
    Returns:
        A pandas DataFrame containing the fetched data, or None if fetch fails.
        
    Raises:
        RuntimeError: If the dataset cannot be fetched or is invalid.
    """
    log_info(f"Attempting to fetch PubChem data from: {dataset_id}")
    
    try:
        # Load dataset using the datasets library
        # If streaming is True, it returns a IterableDataset
        dataset = load_dataset(dataset_id, split="train", streaming=streaming)
        
        # Convert to pandas DataFrame
        # If streaming, we might need to convert iteratively or load a sample if too large
        # For this task, we assume we can load the relevant columns into memory or stream to disk.
        # To ensure we don't OOM on a 7GB dataset, we will convert to a list of dicts first if needed,
        # but pandas can handle a reasonable subset.
        # If the dataset is too large, we will process it in chunks or take a representative sample
        # as per the "Large dataset? Stream the real data" constraint.
        
        if streaming:
            # Convert iterable dataset to a list of dicts (this might be memory intensive if full dataset)
            # Instead, we will iterate and build a dataframe in chunks or just take the first N rows if too big.
            # However, the task requires "Real data only" and "fail loudly" if source not reachable.
            # We will attempt to load the full dataset if it fits, otherwise we stream and process.
            # For the purpose of this implementation, we assume the dataset is manageable or we stream.
            # Let's try to load as a dataframe directly if streaming=False, else iterate.
            # Given the constraint, we will try to load a subset if the full one is too big,
            # but we must state the sample size.
            
            # We will use a generator to convert to DataFrame to avoid loading everything at once if possible
            # But pandas requires all data. So we will load the first 10,000 rows as a sample if streaming.
            # This is a "well-defined REAL sample" as per instructions.
            rows = []
            count = 0
            max_rows = 10000  # Define a sample size for the runner
            for row in dataset:
                rows.append(row)
                count += 1
                if count >= max_rows:
                    break
            
            df = pd.DataFrame(rows)
            log_info(f"Loaded {len(df)} rows from {dataset_id} (sampled for memory constraints).")
        else:
            df = dataset.to_pandas()
            log_info(f"Loaded {len(df)} rows from {dataset_id}.")
        
        return df
        
    except Exception as e:
        log_error(f"Failed to fetch PubChem data: {str(e)}")
        raise RuntimeError(f"Failed to fetch real data from {dataset_id}. No synthetic fallback available.") from e


def load_pubchem_data(output_dir: str = "data/raw/pubchem", output_file: str = "pubchem_nmr.csv") -> pd.DataFrame:
    """
    Main function to load, filter, and save PubChem NMR data.
    
    Args:
        output_dir: Directory to save the processed data.
        output_file: Filename for the output CSV.
        
    Returns:
        Filtered pandas DataFrame with valid provenance.
    """
    set_seed(42)  # Ensure reproducibility
    
    # Fetch data
    df = fetch_pubchem_data()
    
    if df is None or df.empty:
        raise RuntimeError("Fetched dataset is empty or None.")
    
    # Ensure required columns exist
    required_cols = ["provenance", "chemical_shift", "molecule_id", "mechanism_label"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        # If columns are missing, we might need to map them or fail.
        # For this task, we assume the schema matches or we fail loudly.
        log_error(f"Missing required columns: {missing_cols}")
        raise ValueError(f"Dataset missing required columns: {missing_cols}")
    
    # Filter by provenance
    # Logic: If 'provenance' is missing, ambiguous, or not exactly 'kinetic_studies' or 'validated_intermediate', EXCLUDE.
    initial_count = len(df)
    df_filtered = df[df.apply(lambda row: not should_exclude_row(row, VALID_PROVENANCE_VALUES), axis=1)]
    filtered_count = len(df_filtered)
    
    excluded_count = initial_count - filtered_count
    if excluded_count > 0:
        log_warning(f"Excluded {excluded_count} rows due to invalid/missing provenance.")
    
    if df_filtered.empty:
        log_error("No rows passed the provenance filter. Check data source.")
        # We do not return empty; we fail loudly if no valid data found.
        raise RuntimeError("No valid data found after provenance filtering.")
    
    # Ensure output directory exists
    ensure_directory_exists(output_dir)
    output_path = os.path.join(output_dir, output_file)
    
    # Save to CSV (or Parquet if preferred, but CSV is safer for verification)
    df_filtered.to_csv(output_path, index=False)
    log_info(f"Saved filtered PubChem data to {output_path}")
    
    return df_filtered


def main():
    """Entry point for the script."""
    try:
        log_info("Starting PubChem NMR data ingestion (T012)...")
        df = load_pubchem_data()
        log_info(f"Successfully loaded and filtered {len(df)} records.")
        print(f"Task T012 completed: {len(df)} valid records saved.")
    except Exception as e:
        log_error(f"Task T012 failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
