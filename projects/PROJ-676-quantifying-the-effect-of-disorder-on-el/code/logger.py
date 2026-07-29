"""
Numerical stability logging module (Constitution Principle VI).
Provides the NumericalLogger class to log residuals and convergence flags.
"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from code.config import get_config


class NumericalLogger:
    """
    Logger for numerical residuals and convergence metrics.
    Outputs JSON lines to data/metadata/residuals.json.
    """

    def __init__(self, log_file: Optional[str] = None):
        """
        Initialize the logger.
        
        Args:
            log_file: Path to the log file. Defaults to config.METADATA_DIR / 'residuals.json'.
        """
        config = get_config()
        if log_file is None:
            self.log_path = config.METADATA_DIR / 'residuals.json'
        else:
            self.log_path = Path(log_file)
        
        # Ensure directory exists
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Clear existing file if it exists to avoid duplicates on re-runs
        if self.log_path.exists():
            self.log_path.unlink()

    def log_residual(self, norm: float, flag: bool, task: str = "eigh", 
                     L: Optional[int] = None, W: Optional[float] = None,
                     realization_index: Optional[int] = None) -> None:
        """
        Log a residual norm and convergence flag.
        
        Args:
            norm: The residual norm (e.g., ||H*V - V*D||).
            flag: Boolean indicating if the solver converged.
            task: Name of the task (e.g., 'eigh', 'eigsh').
            L: System size (optional, for context).
            W: Disorder strength (optional, for context).
            realization_index: Index of the disorder realization (optional, for context).
        """
        entry = {
            "task": task,
            "timestamp": datetime.now().isoformat(),
            "residual_norm": float(norm),
            "converged": bool(flag),
            "L": int(L) if L is not None else None,
            "W": float(W) if W is not None else None,
            "realization_index": int(realization_index) if realization_index is not None else None
        }
        
        with open(self.log_path, 'a') as f:
            f.write(json.dumps(entry) + '\n')

    def log_convergence(self, metric: Dict[str, Any]) -> None:
        """
        Log a convergence metric dictionary.
        
        Args:
            metric: Dictionary containing convergence data.
        """
        entry = {
            "task": "convergence",
            "timestamp": datetime.now().isoformat(),
            "metric": metric
        }
        
        with open(self.log_path, 'a') as f:
            f.write(json.dumps(entry) + '\n')


def get_logger() -> NumericalLogger:
    """
    Factory function to get a NumericalLogger instance.
    
    Returns:
        NumericalLogger: A configured logger instance.
    """
    return NumericalLogger()
