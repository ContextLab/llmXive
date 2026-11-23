import os
import logging
import hashlib
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd
from src.utils.logging import get_logger

# Define the specific 5-year windows as required by the task
WINDOWS = [
    "2000-2004",
    "2005-2009",
    "2010-2014",
    "2015-2019",
    "2020-2024"
]

def partition_by_window(
    df: pd.DataFrame,
    year_column: str = "year"
) -> Dict[str, pd.DataFrame]:
    """
    Partition a DataFrame of abstracts into specific 5-year windows.
    
    Args:
        df: DataFrame containing abstract records with a 'year' column.
        year_column: Name of the column containing publication year.
        
    Returns:
        Dictionary mapping window string (e.g., "2000-2004") to 
        the corresponding DataFrame subset.
    """
    logger = get_logger(__name__)
    partitions = {}
    
    for window in WINDOWS:
        start_year, end_year = map(int, window.split("-"))
        mask = (df[year_column] >= start_year) & (df[year_column] <= end_year)
        subset = df[mask].copy()
        partitions[window] = subset
        
        logger.info(f"Window {window}: {len(subset)} records retained "
                    f"out of {len(df)} total ({100*len(subset)/len(df):.2f}%)")
        
        if len(subset) == 0:
            logger.warning(f"Window {window} contains no records!")
            
    return partitions

def compute_checksum(df: pd.DataFrame) -> str:
    """
    Compute a SHA256 checksum of the DataFrame contents for reproducibility.
    
    Args:
        df: DataFrame to checksum.
        
    Returns:
        Hexadecimal string of the SHA256 hash.
    """
    # Convert to JSON string to ensure consistent hashing across types
    data_str = df.to_json(orient="records", lines=False)
    return hashlib.sha256(data_str.encode('utf-8')).hexdigest()

def save_partitioned_csvs(
    partitions: Dict[str, pd.DataFrame],
    output_dir: str,
    base_filename: str = "processed_abstracts"
) -> Dict[str, str]:
    """
    Save each window partition to a separate CSV file and compute checksums.
    
    Args:
        partitions: Dictionary of window name -> DataFrame.
        output_dir: Directory path where CSVs will be saved.
        base_filename: Base name for output files.
        
    Returns:
        Dictionary mapping window name to the path of the saved CSV file.
    """
    logger = get_logger(__name__)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    saved_files = {}
    checksums = {}
    
    for window, df in partitions.items():
        if len(df) == 0:
            logger.warning(f"Skipping save for {window} as it is empty.")
            continue
        
        filename = f"{base_filename}_{window}.csv"
        file_path = output_path / filename
        
        # Save to CSV
        df.to_csv(file_path, index=False)
        saved_files[window] = str(file_path)
        
        # Compute and store checksum
        checksum = compute_checksum(df)
        checksums[window] = checksum
        
        logger.info(f"Saved {window} partition: {file_path} "
                    f"(records={len(df)}, checksum={checksum[:16]}...)")
                    
    return saved_files, checksums

def main():
    """
    Main entry point for the saver module.
    Loads preprocessed data (from tokenized/filter stage), partitions by window,
    and saves to data/processed/.
    """
    logger = get_logger(__name__)
    logger.info("Starting data storage and partitioning process...")
    
    # Define paths
    # Assuming the previous stage (T015) outputs to data/raw/tokenized.jsonl
    # or similar. We need to load the filtered data.
    # Based on the pipeline flow: Fetch -> Raw JSONL -> Tokenize/Filter -> Processed CSV
    
    # We will look for the tokenized/filtered data. 
    # The filter.py (T015) likely outputs to a specific location or we read from the
    # raw tokenized results if not saved separately.
    # For this implementation, we assume the filter stage produced a JSONL file 
    # or we load from the tokenized results saved by tokenizer.py.
    
    # Let's assume the filter stage saved to: data/raw/filtered_abstracts.jsonl
    # If not found, we try to load from the tokenized results if they were saved there.
    
    input_file_candidates = [
        Path("data/raw/filtered_abstracts.jsonl"),
        Path("data/raw/tokenized_abstracts.jsonl"),
        Path("data/raw/preprocessed_abstracts.jsonl")
    ]
    
    input_path = None
    for candidate in input_file_candidates:
        if candidate.exists():
            input_path = candidate
            break
            
    if not input_path:
        # Fallback: try to load from the tokenized results if they exist in a specific format
        # Or raise an error if no data is found.
        # We must fail loudly if no real data is found.
        raise FileNotFoundError(
            "No preprocessed data file found in data/raw/. "
            "Ensure T015 (filter) has been executed and output a JSONL file."
        )
        
    logger.info(f"Loading preprocessed data from: {input_path}")
    
    # Load data
    try:
        df = pd.read_json(input_path, lines=True)
    except ValueError:
        # Try loading as regular JSON if not lines
        with open(input_path, 'r') as f:
            import json
            data = json.load(f)
            if isinstance(data, list):
                df = pd.DataFrame(data)
            else:
                raise ValueError(f"Unexpected JSON structure in {input_path}")
                
    logger.info(f"Loaded {len(df)} records from {input_path}")
    
    if df.empty:
        raise ValueError("Loaded data is empty. Check the upstream filtering logic.")
        
    # Ensure year column exists and is numeric
    if "year" not in df.columns:
        raise KeyError("Data must contain a 'year' column for partitioning.")
        
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df = df.dropna(subset=["year"])
    
    if df.empty:
        raise ValueError("No valid records with numeric year found.")
        
    # Partition by window
    partitions = partition_by_window(df)
    
    # Save partitions
    output_dir = "data/processed"
    saved_files, checksums = save_partitioned_csvs(partitions, output_dir)
    
    if not saved_files:
        raise RuntimeError("No files were saved. Check partitioning logic.")
        
    logger.info("Partitioning and saving completed successfully.")
    logger.info(f"Saved files: {list(saved_files.values())}")
    
    # Optionally save a manifest for this step
    manifest = {
        "source_file": str(input_path),
        "windows": list(partitions.keys()),
        "record_counts": {w: len(partitions[w]) for w in partitions},
        "checksums": checksums,
        "output_files": saved_files
    }
    
    manifest_path = Path(output_dir) / "partition_manifest.json"
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
        
    logger.info(f"Saved partition manifest to {manifest_path}")
    
    return saved_files, checksums

if __name__ == "__main__":
    main()
