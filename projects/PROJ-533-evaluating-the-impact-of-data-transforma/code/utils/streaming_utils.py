"""
Streaming utilities for processing large datasets that exceed RAM limits.

This module provides functions to load data in chunks and compute online
statistics (mean, variance) for large files without loading the entire
dataset into memory.
"""
import os
import csv
import logging
import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Generator, Any, Union
import numpy as np

from code.utils.logging_config import get_logger

logger: logging.Logger = get_logger(__name__)


def stream_csv_rows(
    file_path: str,
    delimiter: str = ',',
    chunk_size: int = 10000
) -> Generator[List[str], None, None]:
    """
    Stream rows from a CSV file in chunks.
    
    Args:
        file_path: Path to the CSV file.
        delimiter: CSV delimiter character.
        chunk_size: Number of rows to yield at a time.
        
    Yields:
        Lists of row values (strings).
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is empty or malformed.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    try:
        with open(file_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter=delimiter)
            header = next(reader, None)
            
            if header is None:
                raise ValueError("CSV file is empty or has no header.")
            
            yield header
            
            count = 0
            current_chunk: List[List[str]] = []
            
            for row in reader:
                current_chunk.append(row)
                count += 1
                
                if count >= chunk_size:
                    yield from current_chunk
                    current_chunk = []
                    count = 0
            
            if current_chunk:
                yield from current_chunk
                
    except csv.Error as e:
        logger.error(f"CSV parsing error in {file_path}: {e}")
        raise
    except UnicodeDecodeError as e:
        logger.error(f"Encoding error in {file_path}: {e}")
        raise


class OnlineStatsCalculator:
    """
    Welford's online algorithm for computing mean and variance in a single pass.
    
    This is memory-efficient and numerically stable for streaming data.
    """
    
    def __init__(self, n_features: int):
        """
        Initialize the calculator.
        
        Args:
            n_features: Number of columns/features to track.
        """
        self.n = 0
        self.mean = np.zeros(n_features)
        self.M2 = np.zeros(n_features)
        self.n_features = n_features
        
    def update(self, x: np.ndarray) -> None:
        """
        Update statistics with a new batch of data.
        
        Args:
            x: Array of shape (n_samples, n_features) with new data points.
        """
        if x.ndim == 1:
            x = x.reshape(-1, 1)
            
        if x.shape[1] != self.n_features:
            raise ValueError(
                f"Expected {self.n_features} features, got {x.shape[1]}"
            )
        
        batch_size = x.shape[0]
        
        for i in range(batch_size):
            self.n += 1
            delta = x[i] - self.mean
            self.mean += delta / self.n
            delta2 = x[i] - self.mean
            self.M2 += delta * delta2
            
    def get_mean(self) -> np.ndarray:
        """Return the current mean vector."""
        return self.mean.copy()
        
    def get_variance(self, ddof: int = 0) -> np.ndarray:
        """
        Return the current variance vector.
        
        Args:
            ddof: Delta degrees of freedom. divisor = n - ddof.
        """
        if self.n < 2 and ddof >= 1:
            return np.full(self.n_features, np.nan)
        
        return self.M2 / (self.n - ddof)
        
    def get_std(self, ddof: int = 0) -> np.ndarray:
        """Return the current standard deviation vector."""
        return np.sqrt(self.get_variance(ddof))
        
    def get_count(self) -> int:
        """Return the total number of samples processed."""
        return self.n


def compute_online_stats(
    file_path: str,
    columns: Optional[List[str]] = None,
    delimiter: str = ',',
    chunk_size: int = 10000
) -> Tuple[Dict[str, Dict[str, float]], int]:
    """
    Compute mean and variance for specified columns in a large CSV file
    using streaming (Welford's algorithm).
    
    Args:
        file_path: Path to the CSV file.
        columns: List of column names to compute stats for. If None, all
                 numeric columns are used.
        delimiter: CSV delimiter character.
        chunk_size: Number of rows to process per chunk.
        
    Returns:
        A tuple containing:
            - stats_dict: Dict mapping column names to {'mean': float, 'var': float, 'n': int}
            - total_rows: Total number of data rows processed (excluding header)
            
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If no numeric columns are found or parsing fails.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
        
    logger.info(f"Starting streaming stats computation for {file_path}")
    
    rows_stream = stream_csv_rows(file_path, delimiter, chunk_size)
    header = next(rows_stream)
    
    # Determine column indices
    if columns is None:
        # Auto-detect numeric columns
        col_indices = []
        for i, val in enumerate(header):
            try:
                float(val)
                col_indices.append(i)
            except ValueError:
                pass
        if not col_indices:
            raise ValueError("No numeric columns found in the file.")
        columns = [header[i] for i in col_indices]
        col_indices = list(range(len(col_indices)))
    else:
        col_indices = []
        for col in columns:
            try:
                idx = header.index(col)
                col_indices.append(idx)
            except ValueError:
                raise ValueError(f"Column '{col}' not found in header.")
                
    n_features = len(col_indices)
    calculator = OnlineStatsCalculator(n_features)
    
    total_rows = 0
    
    for chunk in rows_stream:
        # chunk is a list of rows (each row is a list of strings)
        batch = []
        for row in chunk:
            if len(row) != len(header):
                logger.warning(f"Skipping malformed row: {row}")
                continue
                
            try:
                values = [float(row[i]) for i in col_indices]
                batch.append(values)
            except ValueError:
                # Skip rows with non-numeric values in target columns
                continue
                
        if batch:
            batch_array = np.array(batch)
            calculator.update(batch_array)
            total_rows += len(batch)
            
    if total_rows == 0:
        raise ValueError("No valid numeric data rows found.")
        
    stats_dict = {}
    means = calculator.get_mean()
    vars_ = calculator.get_variance(ddof=0)
    
    for i, col in enumerate(columns):
        stats_dict[col] = {
            'mean': float(means[i]),
            'var': float(vars_[i]),
            'n': total_rows
        }
        
    logger.info(
        f"Completed streaming stats for {file_path}: {total_rows} rows processed"
    )
    
    return stats_dict, total_rows


def stream_numeric_data(
    file_path: str,
    columns: Optional[List[str]] = None,
    delimiter: str = ',',
    chunk_size: int = 10000
) -> Generator[np.ndarray, None, None]:
    """
    Stream numeric data from a CSV file as numpy arrays.
    
    Args:
        file_path: Path to the CSV file.
        columns: List of column names to extract. If None, all numeric columns.
        delimiter: CSV delimiter character.
        chunk_size: Number of rows per chunk.
        
    Yields:
        NumPy arrays of shape (n_rows_in_chunk, n_features).
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If parsing fails or no numeric data found.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
        
    rows_stream = stream_csv_rows(file_path, delimiter, chunk_size)
    header = next(rows_stream)
    
    # Determine column indices
    if columns is None:
        col_indices = []
        for i, val in enumerate(header):
            try:
                float(val)
                col_indices.append(i)
            except ValueError:
                pass
        if not col_indices:
            raise ValueError("No numeric columns found in the file.")
        columns = [header[i] for i in col_indices]
    else:
        col_indices = []
        for col in columns:
            try:
                idx = header.index(col)
                col_indices.append(idx)
            except ValueError:
                raise ValueError(f"Column '{col}' not found in header.")
                
    for chunk in rows_stream:
        batch = []
        for row in chunk:
            if len(row) != len(header):
                continue
            try:
                values = [float(row[i]) for i in col_indices]
                batch.append(values)
            except ValueError:
                continue
                
        if batch:
            yield np.array(batch)


def get_file_row_count(file_path: str, delimiter: str = ',') -> int:
    """
    Count the number of data rows in a CSV file (excluding header) efficiently.
    
    Args:
        file_path: Path to the CSV file.
        delimiter: CSV delimiter character.
        
    Returns:
        Number of data rows.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
        
    count = 0
    with open(file_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter=delimiter)
        next(reader, None)  # Skip header
        for _ in reader:
            count += 1
            
    return count
