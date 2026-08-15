"""
Raw data capture and hygiene module for Constitution Principle III compliance.

This module handles the generation, storage, and checksumming of raw matrix
instances and intermediate states before any aggregation occurs.
"""
import os
import logging
import json
import time
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import numpy as np
from scipy import sparse

from utils.config import get_project_paths, ensure_directories
from utils.checksum import compute_file_checksum, save_checksum_manifest

logger = logging.getLogger(__name__)


def save_dense_matrix_to_npy(matrix: np.ndarray, output_path: Path, metadata: Dict[str, Any]) -> str:
    """
    Save a dense matrix to .npy format and return its checksum.
    
    Args:
        matrix: The dense numpy array to save.
        output_path: The full path where the .npy file will be saved.
        metadata: Dictionary containing metadata about the matrix (seed, N, theta, etc.).
        
    Returns:
        str: The SHA-256 checksum of the saved file.
    """
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save matrix
    np.save(str(output_path), matrix)
    
    # Compute checksum
    checksum = compute_file_checksum(output_path)
    
    # Save metadata alongside
    metadata_path = output_path.with_suffix('.json')
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
        
    logger.info(f"Saved dense matrix to {output_path} (checksum: {checksum[:16]}...)")
    return checksum


def save_sparse_matrix_to_npz(matrix: sparse.csr_matrix, output_path: Path, metadata: Dict[str, Any]) -> str:
    """
    Save a sparse matrix to .npz format and return its checksum.
    
    Args:
        matrix: The sparse scipy matrix to save.
        output_path: The full path where the .npz file will be saved.
        metadata: Dictionary containing metadata about the matrix.
        
    Returns:
        str: The SHA-256 checksum of the saved file.
    """
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save matrix
    sparse.save_npz(str(output_path), matrix)
    
    # Compute checksum
    checksum = compute_file_checksum(output_path)
    
    # Save metadata alongside
    metadata_path = output_path.with_suffix('.json')
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
        
    logger.info(f"Saved sparse matrix to {output_path} (checksum: {checksum[:16]}...)")
    return checksum


def capture_and_checksum_raw_instance(
    matrix: np.ndarray,
    perturbation: Optional[np.ndarray] = None,
    perturbation_type: str = "diagonal",
    seed: int = 0,
    N: int = 1000,
    theta: float = 2.5,
    sparsity_density: Optional[float] = None,
    output_dir: Optional[Path] = None
) -> Dict[str, str]:
    """
    Capture a raw matrix instance, save it, and compute its checksum.
    
    This function satisfies Constitution Principle III (Data Hygiene) by ensuring
    that raw data is preserved and checksummed before any aggregation or analysis.
    
    Args:
        matrix: The raw Wigner matrix (N x N).
        perturbation: Optional perturbation matrix applied to the Wigner matrix.
        perturbation_type: Type of perturbation ("diagonal", "block-sparse", "random-sparse").
        seed: Random seed used for generation.
        N: Matrix dimension.
        theta: Perturbation norm.
        sparsity_density: Density if sparse perturbation was used.
        output_dir: Directory to save raw data. Defaults to data/raw/ from config.
        
    Returns:
        Dictionary containing file paths and checksums for all saved artifacts.
    """
    if output_dir is None:
        paths = get_project_paths()
        output_dir = paths["data_raw"]
        
    ensure_directories([output_dir])
    
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    run_id = f"N{N}_theta{theta:.2f}_seed{seed}"
    
    results = {}
    
    # Save Wigner matrix
    wigner_path = output_dir / f"wigner_{run_id}.npy"
    wigner_meta = {
        "type": "wigner",
        "N": N,
        "seed": seed,
        "timestamp": timestamp,
        "perturbation_applied": perturbation is not None,
        "perturbation_type": perturbation_type,
        "theta": theta,
        "sparsity_density": sparsity_density
    }
    results["wigner_path"] = str(wigner_path)
    results["wigner_checksum"] = save_dense_matrix_to_npy(matrix, wigner_path, wigner_meta)
    
    # Save perturbation if provided
    if perturbation is not None:
        pert_path = output_dir / f"perturbation_{run_id}.npy"
        pert_meta = {
            "type": perturbation_type,
            "N": N,
            "seed": seed,
            "timestamp": timestamp,
            "theta": theta,
            "sparsity_density": sparsity_density
        }
        results["perturbation_path"] = str(pert_path)
        results["perturbation_checksum"] = save_dense_matrix_to_npy(perturbation, pert_path, pert_meta)
        
        # Save combined matrix (W + P)
        combined = matrix + perturbation
        combined_path = output_dir / f"combined_{run_id}.npy"
        combined_meta = {
            "type": "combined",
            "N": N,
            "seed": seed,
            "timestamp": timestamp,
            "components": ["wigner", perturbation_type],
            "theta": theta,
            "sparsity_density": sparsity_density
        }
        results["combined_path"] = str(combined_path)
        results["combined_checksum"] = save_dense_matrix_to_npy(combined, combined_path, combined_meta)
    
    logger.info(f"Raw data capture complete for run {run_id}. Checksums: {results['wigner_checksum'][:16]}...")
    return results


def run_hygiene_capture(
    matrices: Dict[str, np.ndarray],
    run_metadata: Dict[str, Any],
    output_dir: Optional[Path] = None
) -> Dict[str, str]:
    """
    Run hygiene capture for multiple matrix instances (e.g., intermediate states).
    
    Args:
        matrices: Dictionary mapping state names to numpy arrays.
        run_metadata: Metadata for the run (seed, N, theta, etc.).
        output_dir: Directory to save raw data.
        
    Returns:
        Dictionary of file paths and checksums.
    """
    if output_dir is None:
        paths = get_project_paths()
        output_dir = paths["data_raw"]
        
    ensure_directories([output_dir])
    
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    run_id = f"run_{timestamp}"
    
    results = {}
    
    for state_name, matrix in matrices.items():
        safe_name = state_name.replace(" ", "_").replace("(", "").replace(")", "")
        file_path = output_dir / f"{safe_name}_{run_id}.npy"
        
        meta = {
            "state_name": state_name,
            "N": matrix.shape[0],
            "timestamp": timestamp,
            **run_metadata
        }
        
        checksum = save_dense_matrix_to_npy(matrix, file_path, meta)
        results[state_name] = {
            "path": str(file_path),
            "checksum": checksum
        }
        
    # Save a manifest of all captured files
    manifest_path = output_dir / f"manifest_{run_id}.json"
    manifest = {
        "run_id": run_id,
        "timestamp": timestamp,
        "metadata": run_metadata,
        "files": results
    }
    
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
        
    results["manifest_path"] = str(manifest_path)
    results["manifest_checksum"] = compute_file_checksum(manifest_path)
    
    logger.info(f"Hygiene capture complete for {len(matrices)} matrices. Manifest: {manifest_path}")
    return results


def main():
    """
    Main entry point for raw data capture demonstration.
    
    This script generates a sample Wigner matrix, applies a perturbation,
    captures the raw instances, and writes checksums to disk.
    """
    import argparse
    from generators.wigner import generate_wigner_matrix
    from generators.perturbation import create_perturbation
    
    parser = argparse.ArgumentParser(description="Capture and checksum raw matrix instances")
    parser.add_argument("--N", type=int, default=1000, help="Matrix dimension")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--theta", type=float, default=2.5, help="Perturbation norm")
    parser.add_argument("--perturbation-type", type=str, default="diagonal", 
                      choices=["diagonal", "block-sparse", "random-sparse"],
                      help="Type of perturbation")
    parser.add_argument("--sparsity-density", type=float, default=0.1,
                      help="Sparsity density for sparse perturbations")
    args = parser.parse_args()
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger.info(f"Starting raw data capture: N={args.N}, seed={args.seed}, "
               f"theta={args.theta}, type={args.perturbation_type}")
    
    # Generate Wigner matrix
    np.random.seed(args.seed)
    wigner = generate_wigner_matrix(args.N)
    
    # Create perturbation
    perturbation = create_perturbation(
        args.N, 
        args.theta, 
        perturbation_type=args.perturbation_type,
        sparsity_density=args.sparsity_density,
        seed=args.seed
    )
    
    # Capture and checksum
    paths = get_project_paths()
    output_dir = paths["data_raw"]
    
    results = capture_and_checksum_raw_instance(
        matrix=wigner,
        perturbation=perturbation,
        perturbation_type=args.perturbation_type,
        seed=args.seed,
        N=args.N,
        theta=args.theta,
        sparsity_density=args.sparsity_density if args.perturbation_type != "diagonal" else None,
        output_dir=output_dir
    )
    
    # Save checksum manifest
    manifest_path = output_dir / "checksum_manifest.json"
    save_checksum_manifest([results], manifest_path)
    
    logger.info("Raw data capture and checksumming complete.")
    logger.info(f"Results: {json.dumps(results, indent=2)}")
    logger.info(f"Manifest saved to: {manifest_path}")


if __name__ == "__main__":
    main()
