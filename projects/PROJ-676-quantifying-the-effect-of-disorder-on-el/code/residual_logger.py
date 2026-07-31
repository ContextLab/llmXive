import json
import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from config import get_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def log_eigenvalue_residual(
    residual_norm: float,
    task: str,
    L: int,
    W: float,
    realization_index: int,
    converged: bool,
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Log a single eigenvalue residual entry.
    
    Args:
        residual_norm: The calculated residual norm (||Hv - λv||)
        task: 'eigh' or 'tm'
        L: System size
        W: Disorder width
        realization_index: Index of the disorder realization
        converged: Whether the solver converged
        output_path: Optional path to write immediately. If None, returns the dict.
    
    Returns:
        The log entry dictionary.
    """
    entry = {
        'timestamp': datetime.now().isoformat(),
        'task': task,
        'L': L,
        'W': W,
        'realization_index': realization_index,
        'residual_norm': float(residual_norm),
        'converged': converged
    }
    
    if output_path:
        append_residuals_to_file(entry, output_path)
    
    return entry

def save_residuals_to_file(entries: List[Dict[str, Any]], output_path: str) -> None:
    """
    Save a list of residual entries to a JSON lines file.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        for entry in entries:
            f.write(json.dumps(entry) + '\n')
    logger.info(f"Saved {len(entries)} residual entries to {output_path}")

def append_residuals_to_file(entry: Dict[str, Any], output_path: str) -> None:
    """
    Append a single residual entry to a JSON lines file.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'a') as f:
        f.write(json.dumps(entry) + '\n')

def main():
    """
    Entry point to initialize or validate the residual logging infrastructure.
    This script ensures the file exists and can be written to.
    In a real run, this would be invoked by the analysis scripts (T012/T020b)
    to flush logs, but for T017/T015 compliance, we ensure the path is valid.
    """
    config = get_config()
    output_path = str(config.DATA_METADATA_DIR / 'residuals.json')
    
    logger.info(f"Residual Logger initialization. Target: {output_path}")
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # If file doesn't exist, create it empty to ensure path validity
    if not os.path.exists(output_path):
        with open(output_path, 'w') as f:
            pass
        logger.info(f"Created empty residual log file: {output_path}")
    else:
        logger.info(f"Residual log file exists: {output_path}")
    
    # Log a dummy entry to verify write permissions (optional, can be removed if strict)
    # We will NOT log dummy data to avoid polluting real results, 
    # but we ensure the infrastructure is ready.
    logger.info("Residual logger infrastructure ready.")

if __name__ == '__main__':
    main()
