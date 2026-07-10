"""
Utility functions for memory estimation and subsampling triggers.
"""
import os
from pathlib import Path
from typing import Optional


def estimate_memory_usage(file_path: str, sample_lines: int = 1000) -> float:
    """
    Perform linear extrapolation from the first `sample_lines` of the input file
    to predict total RAM usage in MB.

    This function reads the first `sample_lines` of the specified file to determine
    the average bytes per line. It then multiplies this average by the total number
    of lines in the file to estimate the total file size. The result is converted
    to Megabytes (MB).

    Args:
        file_path (str): Path to the input file (e.g., raw DEM output).
        sample_lines (int): Number of lines to sample for the calculation. Defaults to 1000.

    Returns:
        float: Estimated total RAM usage in MB.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is empty or unreadable.
    """
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {file_path}")
    
    if not path.is_file():
        raise ValueError(f"Path is not a file: {file_path}")

    total_bytes = 0
    line_count_sample = 0
    total_line_count = 0

    # First pass: count total lines and sample the first N lines for size
    # We use a buffered read to handle large files efficiently
    try:
        with open(path, 'rb') as f:
            # Count total lines first (efficient seek-based counting is hard for arbitrary text,
            # so we iterate. For very large files, this might be slow, but it's accurate.)
            # Optimization: If the file is massive, we might rely on os.stat size, 
            # but the prompt specifically asks for linear extrapolation from lines.
            
            # To avoid a full double-pass if the file is huge, we can:
            # 1. Sample first N lines.
            # 2. Count total lines.
            
            # Sample first N lines
            for _ in range(sample_lines):
                line = f.readline()
                if not line:
                    break
                total_bytes += len(line)
                line_count_sample += 1
            
            if line_count_sample == 0:
                raise ValueError("File is empty or unreadable.")

            avg_bytes_per_line = total_bytes / line_count_sample

            # Count remaining lines
            remaining_lines = 0
            while f.readline():
                remaining_lines += 1
            
            total_line_count = line_count_sample + remaining_lines

    except PermissionError:
        raise PermissionError(f"Permission denied reading file: {file_path}")
    except Exception as e:
        raise RuntimeError(f"Error reading file {file_path}: {e}")

    if total_line_count == 0:
        raise ValueError("File contains no lines.")

    estimated_total_bytes = avg_bytes_per_line * total_line_count
    estimated_mb = estimated_total_bytes / (1024 * 1024)

    return estimated_mb


def check_subsample_trigger(file_path: str, sample_lines: int = 1000, threshold_mb: float = 6144.0) -> bool:
    """
    Compare the estimated memory usage of a file against a threshold to determine
    if subsampling is required.

    This function uses `estimate_memory_usage` to predict the RAM needed to process
    the input file. If the estimated usage exceeds the specified threshold (default
    is 6GB = 6144 MB), it returns True, signaling that a subsampling strategy should
    be triggered.

    Args:
        file_path (str): Path to the input file.
        sample_lines (int): Number of lines to sample for memory estimation. Defaults to 1000.
        threshold_mb (float): Memory threshold in Megabytes. Defaults to 6144.0 (6GB).

    Returns:
        bool: True if estimated memory usage > threshold_mb (subsample trigger), False otherwise.

    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If the file is empty or unreadable.
    """
    estimated_mb = estimate_memory_usage(file_path, sample_lines)
    return estimated_mb > threshold_mb