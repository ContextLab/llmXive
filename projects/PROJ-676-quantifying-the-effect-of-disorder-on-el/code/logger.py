"""
Numerical logging infrastructure for eigenvalue problem residuals and convergence.
Implements Constitution Principle VI: Log residuals and convergence flags for every eigenvalue problem.
"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from code.config import get_config

class NumericalLogger:
    """
    Logs numerical residuals and convergence flags for eigenvalue problems.
    Output format: JSON lines appended to data/metadata/residuals.json.
    """
    
    def __init__(self, log_path: Optional[str] = None):
        """
        Initialize the logger.
        
        Args:
            log_path: Path to the residuals JSON file. Defaults to config path.
        """
        config = get_config()
        self.log_path = Path(log_path) if log_path else config.RESIDUALS_PATH
        
        # Ensure directory exists
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize file if it doesn't exist
        if not self.log_path.exists():
            with open(self.log_path, 'w') as f:
                pass  # Create empty file

    def log_residual(self, norm: float, flag: bool, task: str = "eigh", 
                    L: int = 0, W: float = 0.0, realization_index: int = 0) -> None:
        """
        Log a residual norm and convergence flag.
        
        Args:
            norm: The residual norm (float).
            flag: Convergence flag (True if converged, False otherwise).
            task: The task name (default: "eigh").
            L: System size (default: 0).
            W: Disorder strength (default: 0.0).
            realization_index: Index of the disorder realization (MANDATORY).
        """
        entry = {
            "task": task,
            "L": L,
            "W": float(W),
            "realization_index": int(realization_index),
            "residual_norm": float(norm),
            "converged": bool(flag)
        }
        
        with open(self.log_path, 'a') as f:
            f.write(json.dumps(entry) + '\n')

    def log_convergence(self, metric: Dict[str, Any]) -> None:
        """
        Log convergence metrics for an eigenvalue problem.
        
        Args:
            metric: Dictionary containing convergence information.
        """
        entry = {
            "type": "convergence",
            "timestamp": datetime.now().isoformat(),
            "metrics": metric
        }
        
        # Separate convergence log file
        convergence_path = self.log_path.parent / "convergence.json"
        
        with open(convergence_path, 'a') as f:
            f.write(json.dumps(entry) + '\n')

def get_logger(log_path: Optional[str] = None) -> NumericalLogger:
    """
    Get or create a NumericalLogger instance.
    
    Args:
        log_path: Optional custom path for the log file.
        
    Returns:
        NumericalLogger instance.
    """
    return NumericalLogger(log_path)
