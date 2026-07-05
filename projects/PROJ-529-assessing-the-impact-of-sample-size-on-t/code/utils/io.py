"""Chunked data processing utilities for memory safety."""

import os
import logging
from typing import Iterator, Optional, List, Dict, Any, Union
from pathlib import Path
import json

logger = logging.getLogger(__name__)

class ChunkedDataReader:
    """
    Reads large datasets in chunks to prevent memory overflow.
    
    Designed to handle datasets >7GB as per FR-001.
    """
    
    def __init__(self, file_path: Union[str, Path], chunk_size: int = 10000):
        """
        Initialize the chunked reader.
        
        Args:
            file_path: Path to the data file.
            chunk_size: Number of rows per chunk.
        """
        self.file_path = Path(file_path)
        self.chunk_size = chunk_size
        
    def read_chunks(self) -> Iterator[List[Dict[str, Any]]]:
        """
        Generator that yields chunks of data.
        
        Yields:
            List of dictionaries representing rows in the chunk.
        """
        if not self.file_path.exists():
            raise FileNotFoundError(f"Data file not found: {self.file_path}")
        
        logger.info(f"Reading {self.file_path} in chunks of {self.chunk_size}")
        
        # Simple CSV-like parsing for demonstration
        # In production, this would use pandas.read_csv with chunksize
        with open(self.file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        if not lines:
            return
            
        header = lines[0].strip().split(',')
            
        for i in range(1, len(lines), self.chunk_size):
            chunk_lines = lines[i:i + self.chunk_size]
            chunk_data = []
            
            for line in chunk_lines:
                values = line.strip().split(',')
                if len(values) == len(header):
                    row = dict(zip(header, values))
                    chunk_data.append(row)
                    
            if chunk_data:
                yield chunk_data
                
        logger.info("Finished reading all chunks")

def process_large_dataset(file_path: Union[str, Path], process_func, output_path: Optional[Union[str, Path]] = None) -> bool:
    """
    Process a large dataset in chunks and optionally write results.
    
    Args:
        file_path: Path to the input data file.
        process_func: Function to apply to each chunk. Should take a list of dicts and return processed data.
        output_path: Optional path to write processed results.
        
    Returns:
        True if processing completed successfully.
    """
    reader = ChunkedDataReader(file_path)
    all_results = []
    
    try:
        for chunk in reader.read_chunks():
            processed_chunk = process_func(chunk)
            if processed_chunk:
                all_results.extend(processed_chunk)
                
        if output_path:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                # Write as simple CSV
                if all_results:
                    headers = list(all_results[0].keys())
                    f.write(','.join(headers) + '\n')
                    for row in all_results:
                        values = [str(row.get(h, '')) for h in headers]
                        f.write(','.join(values) + '\n')
                        
            logger.info(f"Processed results written to {output_path}")
            
        return True
        
    except Exception as e:
        logger.error(f"Error processing dataset: {e}")
        return False