import json
import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from code.config import get_config
from code.logger import get_logger, NumericalLogger

def log_eigenvalue_residual(norm: float, converged: bool, task: str = "eigh",
                           L: Optional[int] = None, W: Optional[float] = None,
                           realization_index: Optional[int] = None):
    """
    Log an eigenvalue residual to the residuals file.
    
    Args:
        norm: Residual norm.
        converged: Whether the solver converged.
        task: Task name (e.g., "eigh", "tm").
        L: System size.
        W: Disorder strength.
        realization_index: Realization index.
    """
    logger = get_logger()
    logger.log_residual(norm, converged, task, L, W, realization_index)

def save_residuals_to_file(residuals: List[Dict[str, Any]], output_path: Optional[Path] = None):
    """
    Save a list of residuals to a file.
    
    Args:
        residuals: List of residual dictionaries.
        output_path: Path to the output file.
    """
    if output_path is None:
        config = get_config()
        output_path = config["DATA_METADATA_PATH"] / "residuals.json"
    
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(residuals, f, indent=2)
    
    logging.info(f"Saved {len(residuals)} residuals to {output_path}")

def append_residuals_to_file(residuals: List[Dict[str, Any]], output_path: Optional[Path] = None):
    """
    Append a list of residuals to the existing file (JSON lines format).
    
    Args:
        residuals: List of residual dictionaries.
        output_path: Path to the output file.
    """
    if output_path is None:
        config = get_config()
        output_path = config["DATA_METADATA_PATH"] / "residuals.json"
    
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Ensure file exists
    if not output_path.exists():
        output_path.touch()
    
    with open(output_path, 'a') as f:
        for residual in residuals:
            f.write(json.dumps(residual) + '\n')
    
    logging.info(f"Appended {len(residuals)} residuals to {output_path}")

def main():
    """Main entry point for residual logging demonstration."""
    config = get_config()
    output_path = config["DATA_METADATA_PATH"] / "residuals.json"
    
    # Log a sample residual
    log_eigenvalue_residual(
        norm=1e-7,
        converged=True,
        task="eigh",
        L=100,
        W=1.0,
        realization_index=0
    )
    
    logging.info(f"Sample residual logged to {output_path}")
    
    # Verify file exists and is non-empty
    if output_path.exists() and output_path.stat().st_size > 0:
        logging.info("SUCCESS: Residuals file created and non-empty.")
        return 0
    else:
        logging.error("FAILURE: Residuals file missing or empty.")
        return 1

if __name__ == "__main__":
    exit(main())
