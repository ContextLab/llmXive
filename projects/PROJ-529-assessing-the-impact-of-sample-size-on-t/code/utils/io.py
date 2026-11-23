"""Chunked data processing utilities for memory safety.

Implements FR-001: Handles datasets >7GB by processing in streams/chunks
without loading the entire file into memory.
"""

import os
import logging
import csv
from typing import Iterator, Optional, List, Dict, Any, Union, Callable, TextIO
from pathlib import Path
import json
import gzip

logger = logging.getLogger(__name__)

class ChunkedDataReader:
    """
    Reads large datasets in chunks to prevent memory overflow.

    Designed to handle datasets >7GB as per FR-001.
    Supports CSV and Gzipped CSV (`.csv.gz`) formats.
    """

    def __init__(self, file_path: Union[str, Path], chunk_size: int = 10000, encoding: str = 'utf-8'):
        """
        Initialize the chunked reader.

        Args:
            file_path: Path to the data file.
            chunk_size: Number of rows per chunk.
            encoding: File encoding (default utf-8).
        """
        self.file_path = Path(file_path)
        self.chunk_size = chunk_size
        self.encoding = encoding

        if not self.file_path.exists():
            raise FileNotFoundError(f"Data file not found: {self.file_path}")

        # Detect compression
        self.is_gzip = self.file_path.suffix == '.gz' or str(self.file_path).endswith('.csv.gz')

    def _open_file(self) -> TextIO:
        """Open the file, handling gzip if necessary."""
        if self.is_gzip:
            # Open with text mode for csv.DictReader compatibility
            return gzip.open(self.file_path, 'rt', encoding=self.encoding)
        return open(self.file_path, 'r', encoding=self.encoding)

    def read_chunks(self) -> Iterator[List[Dict[str, Any]]]:
        """
        Generator that yields chunks of data as dictionaries.

        Uses a streaming approach (csv.DictReader) to ensure
        memory usage remains constant regardless of file size.

        Yields:
            List of dictionaries representing rows in the chunk.
        """
        logger.info(f"Reading {self.file_path} in chunks of {self.chunk_size} (Gzip: {self.is_gzip})")

        chunk = []
        try:
            with self._open_file() as f:
                # csv.DictReader reads one row at a time, keeping memory low
                reader = csv.DictReader(f)

                for row in reader:
                    # Convert numeric strings to float/int where appropriate
                    # to ensure data types are consistent for processing
                    processed_row = {}
                    for k, v in row.items():
                        if v is None:
                            processed_row[k] = None
                            continue
                        try:
                            # Try int first
                            processed_row[k] = int(v)
                        except ValueError:
                            try:
                                # Try float
                                processed_row[k] = float(v)
                            except ValueError:
                                # Keep as string
                                processed_row[k] = v
                    
                    chunk.append(processed_row)

                    if len(chunk) >= self.chunk_size:
                        yield chunk
                        chunk = []

                # Yield remaining rows
                if chunk:
                    yield chunk

        except Exception as e:
            logger.error(f"Error reading chunk from {self.file_path}: {e}")
            raise
        finally:
            # Explicitly close if we opened it (context manager handles it, 
            # but good for explicitness in complex logic)
            pass

        logger.info("Finished reading all chunks")


def process_large_dataset(
    file_path: Union[str, Path],
    process_func: Callable[[List[Dict[str, Any]]], List[Dict[str, Any]]],
    output_path: Optional[Union[str, Path]] = None,
    chunk_size: int = 10000
) -> bool:
    """
    Process a large dataset in chunks and optionally write results.

    This function streams the input file, applies `process_func` to each chunk,
    and writes the aggregated results to `output_path` if provided.
    
    Memory usage is bounded by `chunk_size`.

    Args:
        file_path: Path to the input data file (CSV or CSV.gz).
        process_func: Function to apply to each chunk. 
                      Should take a list of dicts and return a list of processed dicts.
        output_path: Optional path to write processed results (CSV).
        chunk_size: Number of rows per chunk.

    Returns:
        True if processing completed successfully.
    """
    reader = ChunkedDataReader(file_path, chunk_size=chunk_size)
    
    # We stream the output if writing to avoid holding everything in memory
    # However, for the return value (bool), we just need success/fail.
    # If output_path is set, we write incrementally.
    
    output_file = Path(output_path) if output_path else None
    output_handle = None
    headers_written = False

    try:
        for chunk in reader.read_chunks():
            if not chunk:
                continue

            processed_chunk = process_func(chunk)
            
            if processed_chunk:
                if output_file:
                    if not headers_written and output_handle:
                        # Write headers
                        headers = list(processed_chunk[0].keys())
                        output_handle.write(','.join(headers) + '\n')
                        headers_written = True
                    
                    if not headers_written and not output_handle:
                        # First time opening
                        output_file.parent.mkdir(parents=True, exist_ok=True)
                        output_handle = open(output_file, 'w', encoding='utf-8', newline='')
                        headers = list(processed_chunk[0].keys())
                        output_handle.write(','.join(headers) + '\n')
                        headers_written = True

                    for row in processed_chunk:
                        values = [str(row.get(h, '')) for h in headers]
                        output_handle.write(','.join(values) + '\n')

        if output_handle:
            output_handle.close()
            logger.info(f"Processed results written to {output_path}")
        
        return True

    except Exception as e:
        logger.error(f"Error processing dataset: {e}")
        if output_handle:
            output_handle.close()
        # Clean up partial output if failed
        if output_file and output_file.exists():
            try:
                os.remove(output_file)
            except OSError:
                pass
        return False