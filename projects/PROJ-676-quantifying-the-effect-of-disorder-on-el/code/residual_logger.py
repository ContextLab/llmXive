"""
Residual logger module.
Provides functions to log and save eigenvalue residuals to data/metadata/residuals.json.
This module is a wrapper around the NumericalLogger class for specific task integration.
"""
import json
import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from code.logger import get_logger, NumericalLogger


logger = logging.getLogger(__name__)
num_logger = get_logger()


def log_eigenvalue_residual(task: str, L: int, W: float, realization_index: int, 
                            residual_norm: float, converged: bool) -> None:
    """
    Log an eigenvalue residual entry.
    
    Args:
        task: Name of the task (e.g., 'eigh', 'eigsh').
        L: System size.
        W: Disorder strength.
        realization_index: Index of the disorder realization.
        residual_norm: The residual norm.
        converged: Boolean indicating convergence.
    """
    num_logger.log_residual(
        norm=residual_norm,
        flag=converged,
        task=task,
        L=L,
        W=W,
        realization_index=realization_index
    )
    logger.debug(f"Logged residual for task={task}, L={L}, W={W}, idx={realization_index}")


def save_residuals_to_file(residuals: List[Dict[str, Any]], output_path: str) -> None:
    """
    Save a list of residual dictionaries to a JSON lines file.
    
    Args:
        residuals: List of residual entries.
        output_path: Path to the output file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w') as f:
        for entry in residuals:
            f.write(json.dumps(entry) + '\n')
    logger.info(f"Saved {len(residuals)} residuals to {output_path}")


def append_residuals_to_file(residuals: List[Dict[str, Any]], output_path: str) -> None:
    """
    Append a list of residual dictionaries to a JSON lines file.
    
    Args:
        residuals: List of residual entries.
        output_path: Path to the output file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'a') as f:
        for entry in residuals:
            f.write(json.dumps(entry) + '\n')
    logger.info(f"Appended {len(residuals)} residuals to {output_path}")


def main():
    """
    Main entry point for residual logging demonstration.
    This function is invoked by the orchestration pipeline to ensure the logger is active.
    """
    logger.info("Residual logger module initialized.")
    # Example usage
    log_eigenvalue_residual(
        task="eigh",
        L=100,
        W=1.0,
        realization_index=0,
        residual_norm=1e-12,
        converged=True
    )
    logger.info("Example residual logged.")


if __name__ == "__main__":
    main()
