import os
import logging
import hashlib
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd
import numpy as np

from src.utils.logging import get_logger
from src.utils.config import ensure_directories
from src.data.preprocess.tokenizer import load_preprocessed_data

logger = get_logger(__name__)

# Define the specific 5-year windows as per project requirements
WINDOWS = [
    "2000-2004",
    "2005-2009",
    "2010-2014",
    "2015-2019",
    "2020-2024"
]

def partition_by_window(records: List[Dict[str, Any]], window_key: str = "year") -> Dict[str, List[Dict[str, Any]]]:
    """
    Partitions a list of abstract records into dictionaries based on the 5-year windows.
    
    Args:
        records: List of dictionaries containing abstract data with a 'year' field.
        window_key: The key in the record dictionary that holds the year.
        
    Returns:
        A dictionary mapping window strings (e.g., "2000-2004") to lists of records.
    """
    partitions: Dict[str, List[Dict[str, Any]]] = {w: [] for w in WINDOWS}
    
    for record in records:
        try:
            year = int(record.get(window_key, 0))
            assigned = False
            for window in WINDOWS:
                start, end = map(int, window.split("-"))
                if start <= year <= end:
                    partitions[window].append(record)
                    assigned = True
                    break
            
            if not assigned:
                logger.debug(f"Record year {year} does not fall into any defined 5-year window.")
        except (ValueError, TypeError):
            logger.warning(f"Could not parse year from record: {record.get('id', 'unknown')}")
            
    return partitions

def compute_checksum(df: pd.DataFrame) -> str:
    """
    Computes a SHA256 checksum of the DataFrame content for reproducibility verification.
    
    Args:
        df: The pandas DataFrame to checksum.
        
    Returns:
        Hex digest of the SHA256 hash.
    """
    # Convert to CSV string to ensure consistent hashing regardless of internal dtypes
    csv_content = df.to_csv(index=False).encode('utf-8')
    return hashlib.sha256(csv_content).hexdigest()

def save_partitioned_csvs(
    data_path: Path,
    output_dir: Path,
    window_map: Optional[Dict[str, str]] = None
) -> Dict[str, str]:
    """
    Loads preprocessed data, partitions it by 5-year windows, and saves each partition
    as a separate CSV file in the specified output directory.
    
    Args:
        data_path: Path to the input preprocessed data (JSONL or CSV).
        output_dir: Path to the directory where CSVs will be saved.
        window_map: Optional mapping of window names to specific output filenames.
        
    Returns:
        Dictionary mapping window names to their saved file paths and checksums.
    """
    ensure_directories([output_dir])
    
    logger.info(f"Loading preprocessed data from {data_path}")
    records = load_preprocessed_data(data_path)
    
    if not records:
        logger.warning("No records found to save.")
        return {}
    
    logger.info(f"Loaded {len(records)} records. Partitioning by 5-year windows...")
    partitions = partition_by_window(records)
    
    saved_manifest: Dict[str, Dict[str, str]] = {}
    
    for window_name, window_records in partitions.items():
        if not window_records:
            logger.info(f"No records found for window {window_name}. Skipping.")
            continue
        
        df = pd.DataFrame(window_records)
        
        # Ensure consistent column ordering
        if 'id' in df.columns:
            cols = ['id', 'source', 'year', 'title', 'abstract', 'tokens', 'token_count']
            existing_cols = [c for c in cols if c in df.columns]
            other_cols = [c for c in df.columns if c not in cols]
            df = df[existing_cols + other_cols]
        
        output_filename = window_map.get(window_name, f"{window_name.replace('-', '_')}.csv") if window_map else f"{window_name.replace('-', '_')}.csv"
        output_path = output_dir / output_filename
        
        df.to_csv(output_path, index=False)
        checksum = compute_checksum(df)
        
        saved_manifest[window_name] = {
            "file_path": str(output_path),
            "record_count": len(window_records),
            "checksum": checksum
        }
        
        logger.info(f"Saved {len(window_records)} records to {output_path} (SHA256: {checksum[:16]}...)")
    
    logger.info(f"Partitioning complete. Saved {len(saved_manifest)} window files.")
    return saved_manifest

def main():
    """
    Main entry point for the saver module.
    Loads data from the default processed location and saves partitioned CSVs.
    """
    # Default paths relative to project root
    project_root = Path(__file__).resolve().parents[3]
    input_path = project_root / "data" / "processed" / "preprocessed_abstracts.jsonl"
    output_base = project_root / "data" / "processed"
    
    # Check if input exists, if not, try to find any preprocessed file
    if not input_path.exists():
        # Fallback: look for any jsonl in data/processed
        candidates = list((project_root / "data" / "processed").glob("*.jsonl"))
        if candidates:
            input_path = candidates[0]
            logger.info(f"Using fallback input path: {input_path}")
        else:
            logger.error(f"No preprocessed data found at {input_path} or in {project_root / 'data' / 'processed'}")
            return
    
    save_partitioned_csvs(input_path, output_base)

if __name__ == "__main__":
    main()
