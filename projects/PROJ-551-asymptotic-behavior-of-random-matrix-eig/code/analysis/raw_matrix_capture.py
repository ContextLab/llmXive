"""
Module for capturing and saving raw Wigner matrix instances to disk.

This module implements the logic for T019a: generating and persisting
raw Wigner matrix instances to data/raw/matrix_N{N}_seed{seed}.npy.
"""
import os
import logging
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Any
from generators.wigner import generate_wigner_matrix
from utils.config import get_project_paths, ensure_directories

logger = logging.getLogger(__name__)

def save_raw_wigner_matrix(N: int, seed: int, output_dir: Optional[str] = None) -> Path:
    """
    Generate a Wigner matrix of size N x N with a specific seed and save it to disk.
    
    This function implements the core requirement of T019a:
    - Generates a real Wigner matrix using the existing generator
    - Persists it to data/raw/matrix_N{N}_seed{seed}.npy
    - Returns the path to the saved file for subsequent checksumming (T019)
    
    Args:
        N: Matrix dimension (must be positive integer)
        seed: Random seed for reproducibility
        output_dir: Optional override for output directory (defaults to data/raw)
        
    Returns:
        Path: Absolute path to the saved .npy file
        
    Raises:
        ValueError: If N is not a positive integer
        RuntimeError: If the matrix generation fails
        IOError: If the file cannot be written
    """
    if not isinstance(N, int) or N <= 0:
        raise ValueError(f"N must be a positive integer, got {N}")
    if not isinstance(seed, int):
        raise ValueError(f"seed must be an integer, got {seed}")
    
    # Ensure output directory exists
    project_paths = get_project_paths()
    if output_dir is None:
        output_dir = project_paths["data_raw"]
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Generate the Wigner matrix
    logger.info(f"Generating {N}x{N} Wigner matrix with seed {seed}")
    try:
        matrix = generate_wigner_matrix(N, seed)
    except Exception as e:
        logger.error(f"Failed to generate Wigner matrix: {e}")
        raise RuntimeError(f"Matrix generation failed: {e}")
    
    # Validate the matrix was generated correctly
    if matrix is None:
        raise RuntimeError("generate_wigner_matrix returned None")
    if matrix.shape != (N, N):
        raise RuntimeError(f"Matrix shape mismatch: expected ({N}, {N}), got {matrix.shape}")
    
    # Construct the output filename
    filename = f"matrix_N{N}_seed{seed}.npy"
    file_path = output_path / filename
    
    # Save the matrix to disk
    logger.info(f"Saving matrix to {file_path}")
    try:
        np.save(str(file_path), matrix)
    except Exception as e:
        logger.error(f"Failed to save matrix to {file_path}: {e}")
        raise IOError(f"Could not write matrix file: {e}")
    
    # Verify the file was created
    if not file_path.exists():
        raise IOError(f"File was not created: {file_path}")
    
    file_size = file_path.stat().st_size
    logger.info(f"Successfully saved {N}x{N} Wigner matrix to {file_path} ({file_size} bytes)")
    
    return file_path

def main():
    """
    Command-line entry point for generating a single raw Wigner matrix instance.
    
    Usage:
        python -m analysis.raw_matrix_capture --N 1000 --seed 42
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Generate and save a raw Wigner matrix instance"
    )
    parser.add_argument(
        "--N", 
        type=int, 
        required=True, 
        help="Matrix dimension (e.g., 1000)"
    )
    parser.add_argument(
        "--seed", 
        type=int, 
        required=True, 
        help="Random seed for reproducibility"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory (defaults to data/raw)"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    try:
        file_path = save_raw_wigner_matrix(args.N, args.seed, args.output_dir)
        print(f"Matrix saved to: {file_path}")
        return 0
    except Exception as e:
        logger.error(f"Task failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())