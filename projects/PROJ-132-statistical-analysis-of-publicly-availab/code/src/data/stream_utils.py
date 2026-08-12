"""
Streaming utilities for processing large eBird datasets.

This module provides utilities to stream the verified full eBird dataset
from Hugging Face in chunks to ensure memory usage stays below 6GB.
"""
import logging
import sys
from pathlib import Path
from typing import Generator, Dict, Any, Optional, List
import json

try:
    from datasets import load_dataset
except ImportError:
    print("Error: The 'datasets' library is required. Install with: pip install datasets")
    sys.exit(1)

import polars as pl

from src.config import setup_logging
from src.data.download import compute_sha256

# Configure logging
logger = setup_logging(__name__)

# Constants
CHUNK_SIZE = 100_000
DATASET_NAME = "vvud/eb-data"
MEMORY_LIMIT_GB = 6

def stream_ebird_data(
    split: str = "train",
    chunk_size: int = CHUNK_SIZE,
    dataset_name: str = DATASET_NAME
) -> Generator[pl.DataFrame, None, None]:
    """
    Stream the eBird dataset from Hugging Face in chunks.
    
    Args:
        split: The dataset split to load (default: "train")
        chunk_size: Number of rows per chunk (default: 100,000)
        dataset_name: The Hugging Face dataset identifier
        
    Yields:
        pl.DataFrame: A Polars DataFrame containing up to chunk_size rows
        
    Raises:
        RuntimeError: If the dataset is not available or streaming fails
    """
    logger.info(f"Starting stream of dataset: {dataset_name}, split: {split}")
    
    try:
        # Load dataset in streaming mode
        dataset = load_dataset(
            dataset_name,
            split=split,
            streaming=True
        )
        
        logger.info(f"Successfully connected to {dataset_name}")
        
        # Accumulate rows and yield in chunks
        buffer: List[Dict[str, Any]] = []
        row_count = 0
        
        for row in dataset:
            buffer.append(row)
            row_count += 1
            
            if len(buffer) >= chunk_size:
                # Convert buffer to Polars DataFrame
                df = pl.DataFrame(buffer)
                logger.debug(f"Yielding chunk with {len(df)} rows (total: {row_count})")
                yield df
                buffer = []
        
        # Yield any remaining rows
        if buffer:
            df = pl.DataFrame(buffer)
            logger.info(f"Yielding final chunk with {len(df)} rows (total: {row_count})")
            yield df
            
    except Exception as e:
        logger.error(f"Failed to stream dataset {dataset_name}: {e}")
        raise RuntimeError(f"Dataset streaming failed: {e}") from e

def process_streamed_chunks(
    output_dir: str,
    chunk_size: int = CHUNK_SIZE,
    dataset_name: str = DATASET_NAME
) -> Dict[str, Any]:
    """
    Process streamed chunks and write them to disk as Parquet files.
    
    Args:
        output_dir: Directory to write chunk files
        chunk_size: Number of rows per chunk
        dataset_name: The Hugging Face dataset identifier
        
    Returns:
        Dict containing metadata about the processed chunks
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Processing streamed data to: {output_path}")
    
    chunk_files = []
    total_rows = 0
    checksums = {}
    
    try:
        for i, chunk_df in enumerate(stream_ebird_data(chunk_size=chunk_size, dataset_name=dataset_name)):
            # Write chunk to Parquet
            chunk_file = output_path / f"ebird_chunk_{i:05d}.parquet"
            chunk_df.write_parquet(str(chunk_file))
            chunk_files.append(str(chunk_file))
            
            # Compute checksum
            checksum = compute_sha256(str(chunk_file))
            checksums[str(chunk_file)] = checksum
            
            total_rows += len(chunk_df)
            logger.info(f"Processed chunk {i}: {len(chunk_df)} rows, checksum: {checksum[:16]}...")
            
    except Exception as e:
        logger.error(f"Error processing chunks: {e}")
        raise RuntimeError(f"Chunk processing failed: {e}") from e
    
    # Write checksums manifest
    checksum_file = output_path / "checksums.sha256"
    with open(checksum_file, "w") as f:
        for file_path, checksum in checksums.items():
            f.write(f"{checksum}  {file_path}\n")
    
    # Write metadata
    metadata = {
        "dataset_name": dataset_name,
        "chunk_size": chunk_size,
        "total_chunks": len(chunk_files),
        "total_rows": total_rows,
        "output_dir": str(output_path),
        "checksums": checksums
    }
    
    metadata_file = output_path / "stream_metadata.json"
    with open(metadata_file, "w") as f:
        json.dump(metadata, f, indent=2)
    
    logger.info(f"Streaming complete: {total_rows} rows in {len(chunk_files)} chunks")
    return metadata

def main():
    """Main entry point for streaming eBird data."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Stream eBird data in chunks")
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/raw/ebird_stream",
        help="Output directory for chunked data"
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=CHUNK_SIZE,
        help=f"Number of rows per chunk (default: {CHUNK_SIZE})"
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default=DATASET_NAME,
        help=f"Hugging Face dataset name (default: {DATASET_NAME})"
    )
    
    args = parser.parse_args()
    
    try:
        metadata = process_streamed_chunks(
            output_dir=args.output_dir,
            chunk_size=args.chunk_size,
            dataset_name=args.dataset
        )
        print(f"Successfully streamed data to {args.output_dir}")
        print(f"Total rows: {metadata['total_rows']}")
        print(f"Total chunks: {metadata['total_chunks']}")
    except RuntimeError as e:
        print(f"Failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
