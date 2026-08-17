"""
Raw Matrix Capture Module for User Story 1 (T019a).

This module implements the logic to generate and save raw Wigner matrix
instances to disk as NumPy .npy files. It ensures the matrix is persisted
before any subsequent checksumming operations (T019).
"""

import os
import logging
import numpy as np
from pathlib import Path
from typing import Optional

# Import from existing project API surface
from generators.wigner import generate_wigner_matrix

logger = logging.getLogger(__name__)


def save_raw_wigner_matrix(
    N: int,
    seed: int,
    output_dir: Optional[str] = None,
    perturbation_theta: Optional[float] = None
) -> Path:
    """
    Generate a raw Wigner matrix instance and save it to disk.

    This function strictly adheres to Constitution Principle III (Data Hygiene)
    by persisting the raw data before any derived processing or checksumming.

    Args:
        N: The dimension of the Wigner matrix (N x N).
        seed: The random seed for reproducibility.
        output_dir: Directory to save the matrix. Defaults to 'data/raw'.
        perturbation_theta: Optional theta value for the filename if perturbed.
                            For T019a (raw Wigner), this is typically None,
                            but included for consistency with sweep naming if needed.

    Returns:
        Path: The absolute path to the saved .npy file.

    Raises:
        RuntimeError: If the matrix generation fails or saving fails.
    """
    # Determine output directory
    if output_dir is None:
        # Project root is assumed to be the current working directory or parent of code/
        # Standard convention: data/raw relative to project root
        project_root = Path.cwd()
        # Check if we are running from code/ directory
        if (project_root / "code").exists():
            project_root = project_root
        elif (project_root / "code").parent.name == "code":
            project_root = project_root.parent
        
        output_dir = str(project_root / "data" / "raw")

    output_path_obj = Path(output_dir)
    output_path_obj.mkdir(parents=True, exist_ok=True)

    # Construct filename
    if perturbation_theta is not None:
        filename = f"matrix_N{N}_theta{perturbation_theta}_seed{seed}.npy"
    else:
        filename = f"matrix_N{N}_seed{seed}.npy"
    
    file_path = output_path_obj / filename

    if file_path.exists():
        logger.warning(f"File already exists: {file_path}. Overwriting.")

    logger.info(f"Generating Wigner matrix (N={N}, seed={seed})...")
    
    try:
        # Generate the matrix using the existing API
        # generate_wigner_matrix returns a numpy array
        matrix = generate_wigner_matrix(N, seed)
        
        if not isinstance(matrix, np.ndarray):
            raise TypeError(f"Expected np.ndarray, got {type(matrix)}")
        
        if matrix.shape != (N, N):
            raise ValueError(f"Expected shape ({N}, {N}), got {matrix.shape}")

        logger.info(f"Saving raw matrix to {file_path}...")
        np.save(file_path, matrix)
        
        if not file_path.exists():
            raise RuntimeError(f"Failed to persist file: {file_path}")

        # Verify size
        size_bytes = file_path.stat().st_size
        logger.info(f"Successfully saved raw matrix: {file_path} ({size_bytes} bytes)")
        
        return file_path

    except Exception as e:
        logger.error(f"Failed to generate or save matrix: {e}", exc_info=True)
        raise RuntimeError(f"Matrix generation/persistence failed: {e}") from e


def main():
    """
    CLI entry point for T019a.
    Usage: python -m analysis.raw_matrix_capture --N 1000 --seed 42
    """
    import argparse

    parser = argparse.ArgumentParser(description="Generate and save raw Wigner matrix (T019a)")
    parser.add_argument("--N", type=int, default=1000, help="Matrix dimension")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--output-dir", type=str, default=None, help="Output directory")
    
    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    try:
        file_path = save_raw_wigner_matrix(
            N=args.N,
            seed=args.seed,
            output_dir=args.output_dir
        )
        print(f"SUCCESS: Raw matrix saved to {file_path}")
    except Exception as e:
        print(f"FAILURE: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())