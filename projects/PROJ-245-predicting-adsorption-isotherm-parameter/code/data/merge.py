"""
Merge Chunks Task (T061)

Combines streamed chunk files from data/raw/streamed_chunk_*.parquet
into a single merged dataset at data/raw/merged_dataset.parquet.

Dependencies: T060 (Streaming Data Loader)
"""
import os
import sys
import glob
import logging
from pathlib import Path
from typing import List, Optional

import pandas as pd
import pyarrow.parquet as pq

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/merge_task.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

# Define paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
MERGED_OUTPUT_PATH = RAW_DATA_DIR / "merged_dataset.parquet"
CHUNK_PATTERN = "streamed_chunk_*.parquet"


def ensure_directories() -> None:
    """Ensure output directory exists."""
    MERGED_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured directory exists: {MERGED_OUTPUT_PATH.parent}")


def find_chunk_files(pattern: str = CHUNK_PATTERN, directory: Path = RAW_DATA_DIR) -> List[Path]:
    """
    Find all chunk files matching the pattern in the specified directory.

    Args:
        pattern: Glob pattern to match files (default: streamed_chunk_*.parquet)
        directory: Directory to search in

    Returns:
        List of Path objects for matching files, sorted by name
    """
    search_path = directory / pattern
    files = glob.glob(str(search_path))
    if not files:
        raise FileNotFoundError(
            f"No chunk files found matching '{pattern}' in '{directory}'. "
            f"Please ensure T060 (Streaming Data Loader) has been run successfully."
        )
    
    sorted_files = sorted([Path(f) for f in files])
    logger.info(f"Found {len(sorted_files)} chunk files: {[f.name for f in sorted_files]}")
    return sorted_files


def merge_parquet_files(input_files: List[Path], output_path: Path) -> None:
    """
    Merge multiple Parquet files into a single Parquet file.

    Args:
        input_files: List of input Parquet file paths
        output_path: Output path for the merged file
    """
    if not input_files:
        raise ValueError("No input files provided for merging.")

    logger.info(f"Starting merge of {len(input_files)} files...")
    
    try:
        # Read first file to get schema and initial data
        first_table = pq.read_table(input_files[0])
        logger.info(f"Read first file: {input_files[0].name} - {first_table.num_rows} rows")
        
        # Concatenate remaining files
        if len(input_files) > 1:
            tables = [first_table]
            for i, file_path in enumerate(input_files[1:], 1):
                logger.info(f"Reading chunk {i}/{len(input_files)-1}: {file_path.name}")
                table = pq.read_table(file_path)
                tables.append(table)
            
            # Concatenate all tables
            merged_table = pa.concat_tables(tables)
        else:
            merged_table = first_table

        # Write to output
        pq.write_table(merged_table, output_path)
        
        logger.info(f"Successfully merged {len(input_files)} files into {output_path}")
        logger.info(f"Total rows in merged dataset: {merged_table.num_rows}")
        logger.info(f"Total columns in merged dataset: {merged_table.num_columns}")
        logger.info(f"Column names: {merged_table.column_names}")

    except Exception as e:
        logger.error(f"Error during merge operation: {str(e)}", exc_info=True)
        raise


def main() -> None:
    """Main entry point for the merge task."""
    logger.info("Starting T061: Merge Chunks")
    
    try:
        # Ensure output directory exists
        ensure_directories()
        
        # Find chunk files
        chunk_files = find_chunk_files()
        
        # Merge files
        merge_parquet_files(chunk_files, MERGED_OUTPUT_PATH)
        
        logger.info("T061: Merge Chunks completed successfully")
        
    except FileNotFoundError as e:
        logger.error(f"Missing chunk files: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during merge: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
