import os
import hashlib
import shutil
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Tuple, Optional, List, Dict, Any
from error_handling import DataGapError
from logging_config import get_logger

logger = get_logger(__name__)

def check_disk_usage(path: str = "/") -> bool:
    """
    Check disk usage. Returns True if usage is safe, False if limit exceeded.
    Halts execution if usage > 12 GB (as per project constraints).
    """
    try:
        total, used, free = shutil.disk_usage(path)
        used_gb = used / (2**30)
        if used_gb > 12:
            logger.error(f"Disk usage ({used_gb:.2f} GB) exceeds 12 GB limit.")
            raise DataGapError("Storage Limit Exceeded")
        logger.info(f"Disk usage: {used_gb:.2f} GB / {total / (2**30):.2f} GB")
        return True
    except Exception as e:
        logger.error(f"Error checking disk usage: {e}")
        raise

def compute_sha256(filepath: str) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def verify_sha256(filepath: str, expected_hash: str) -> bool:
    """Verify a file's SHA256 checksum against an expected value."""
    actual_hash = compute_sha256(filepath)
    if actual_hash != expected_hash:
        logger.warning(f"Checksum mismatch for {filepath}: {actual_hash} != {expected_hash}")
        return False
    return True

def load_matrix_from_parquet(filepath: str, column_name: str) -> np.ndarray:
    """Load a matrix from a Parquet file column."""
    try:
        df = pd.read_parquet(filepath)
        if column_name not in df.columns:
            raise DataGapError(f"Column '{column_name}' not found in {filepath}")
        matrix_data = df[column_name].iloc[0]
        if isinstance(matrix_data, list):
            # Handle flattened list if necessary, assuming square matrix
            n = int(len(matrix_data) ** 0.5)
            if n * n != len(matrix_data):
                raise ValueError("Flattened list length is not a perfect square")
            return np.array(matrix_data).reshape(n, n)
        elif isinstance(matrix_data, np.ndarray):
            return matrix_data
        else:
            # Assume it's a string representation or other format
            raise ValueError(f"Unsupported matrix data type: {type(matrix_data)}")
    except Exception as e:
        logger.error(f"Failed to load matrix from {filepath}: {e}")
        raise

def load_matrix_from_file(filepath: str) -> np.ndarray:
    """Load a matrix from a .npy or .csv file."""
    if filepath.endswith('.npy'):
        return np.load(filepath)
    elif filepath.endswith('.csv'):
        return np.loadtxt(filepath, delimiter=',')
    else:
        raise ValueError(f"Unsupported file format: {filepath}")

def validate_matrices_alignment(sc_matrix: np.ndarray, fc_matrix: np.ndarray) -> bool:
    """
    Validate that SC and FC matrices have matching dimensions.
    Halts with a fatal error if dimensions do not match.
    """
    if sc_matrix.shape != fc_matrix.shape:
        msg = (
            f"Dimension mismatch detected: SC matrix shape {sc_matrix.shape} "
            f"does not match FC matrix shape {fc_matrix.shape}. "
            "Cannot proceed with metric calculation."
        )
        logger.error(msg)
        raise DataGapError(msg)
    
    # Additional check for square matrices
    if sc_matrix.shape[0] != sc_matrix.shape[1]:
        msg = f"SC matrix is not square: {sc_matrix.shape}"
        logger.error(msg)
        raise DataGapError(msg)
    
    if fc_matrix.shape[0] != fc_matrix.shape[1]:
        msg = f"FC matrix is not square: {fc_matrix.shape}"
        logger.error(msg)
        raise DataGapError(msg)

    logger.info(f"Matrix validation passed: {sc_matrix.shape}")
    return True

def load_and_validate_subject_matrices(sc_path: str, fc_path: str) -> Tuple[np.ndarray, np.ndarray]:
    """
    Load SC and FC matrices from disk and validate their alignment.
    Returns the loaded matrices if valid.
    """
    sc_matrix = load_matrix_from_file(sc_path)
    fc_matrix = load_matrix_from_file(fc_path)
    validate_matrices_alignment(sc_matrix, fc_matrix)
    return sc_matrix, fc_matrix