import json
import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from code.config import get_config

# Initialize logger for residual tracking
logger = logging.getLogger("residual_logger")

def log_eigenvalue_residual(
    residual_norm: float,
    convergence_flag: bool,
    system_size: int,
    disorder_strength: float,
    realization_index: int,
    eigenvalue_index: int,
    energy: float,
    method: str = "eigh"
) -> Dict[str, Any]:
    """
    Log a single eigenvalue problem residual and convergence status.

    Args:
        residual_norm: ||Hv - λv||_2 norm of the residual
        convergence_flag: True if solver converged successfully
        system_size: L, the dimension of the Hamiltonian
        disorder_strength: W, the disorder parameter
        realization_index: Index of the disorder realization
        eigenvalue_index: Index of the eigenvalue within the sorted spectrum
        energy: The computed eigenvalue
        method: Solver method used ('eigh' or 'eigsh')

    Returns:
        Dictionary containing the log entry data
    """
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "system_size": system_size,
        "disorder_strength": disorder_strength,
        "realization_index": realization_index,
        "eigenvalue_index": eigenvalue_index,
        "energy": energy,
        "residual_norm": residual_norm,
        "converged": convergence_flag,
        "solver_method": method
    }
    
    # Log to console if configured
    if convergence_flag:
        logger.debug(f"Eigenvalue {eigenvalue_index} (E={energy:.6f}): "
                     f"residual={residual_norm:.2e}, converged=True")
    else:
        logger.warning(f"Eigenvalue {eigenvalue_index} (E={energy:.6f}): "
                       f"residual={residual_norm:.2e}, converged=False")
    
    return entry

def save_residuals_to_file(
    residuals: List[Dict[str, Any]],
    output_path: Optional[str] = None
) -> str:
    """
    Save a batch of residual logs to the metadata JSON file.

    Args:
        residuals: List of residual log entries
        output_path: Optional override for output file path

    Returns:
        Path to the written file
    """
    config = get_config()
    if output_path is None:
        output_path = str(config.DATA_METADATA_DIR / "residuals.json")
    
    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing data if file exists
    existing_data = []
    if output_path_obj.exists():
        try:
            with open(output_path_obj, 'r') as f:
                existing_data = json.load(f)
        except (json.JSONDecodeError, IOError):
            # If file is corrupted or empty, start fresh
            existing_data = []
    
    # Append new residuals
    existing_data.extend(residuals)
    
    # Write back with indentation for readability
    with open(output_path_obj, 'w') as f:
        json.dump(existing_data, f, indent=2)
    
    logger.info(f"Saved {len(residuals)} residual entries to {output_path}")
    return output_path

def append_residuals_to_file(
    entry: Dict[str, Any],
    output_path: Optional[str] = None
) -> str:
    """
    Append a single residual entry to the metadata JSON file.
    More efficient for streaming than saving a whole batch.

    Args:
        entry: Single residual log entry
        output_path: Optional override for output file path

    Returns:
        Path to the written file
    """
    config = get_config()
    if output_path is None:
        output_path = str(config.DATA_METADATA_DIR / "residuals.json")
    
    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing data
    existing_data = []
    if output_path_obj.exists():
        try:
            with open(output_path_obj, 'r') as f:
                existing_data = json.load(f)
        except (json.JSONDecodeError, IOError):
            existing_data = []
    
    existing_data.append(entry)
    
    with open(output_path_obj, 'w') as f:
        json.dump(existing_data, f, indent=2)
    
    return output_path

def main():
    """
    Standalone test/demonstration of the residual logger.
    Generates synthetic residual entries to verify file writing.
    """
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Simulate a batch of eigenvalue problems
    test_residuals = []
    for i in range(10):
        residual = log_eigenvalue_residual(
            residual_norm=1e-10 + i * 1e-12,
            convergence_flag=(i % 3 != 0), # Simulate some failures
            system_size=100,
            disorder_strength=1.0,
            realization_index=0,
            eigenvalue_index=i,
            energy=float(i - 5),
            method="eigh"
        )
        test_residuals.append(residual)
    
    # Save to file
    output_file = save_residuals_to_file(test_residuals)
    print(f"Residuals saved to: {output_file}")
    
    # Verify content
    with open(output_file, 'r') as f:
        data = json.load(f)
        print(f"Total entries in file: {len(data)}")
        print(f"First entry: {data[0]}")

if __name__ == "__main__":
    main()
