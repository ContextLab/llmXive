"""
Numerical logging infrastructure for Constitution Principle VI.
Captures numerical residuals and convergence flags for eigenvalue problems.
"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import logging

# Configure logger
logger = logging.getLogger(__name__)

class NumericalLogger:
    """
    Logger for numerical stability metrics (residuals, convergence).
    Writes JSON lines to data/metadata/residuals.json.
    """
    def __init__(self, output_path: Optional[str] = None):
        self.output_path = output_path or "data/metadata/residuals.json"
        self._ensure_directory()

    def _ensure_directory(self):
        """Ensure the output directory exists."""
        Path(self.output_path).parent.mkdir(parents=True, exist_ok=True)

    def log_residual(self, norm: float, flag: bool, task: str = "eigh", **kwargs):
        """
        Log a residual norm and convergence flag.

        Args:
            norm: The residual norm (float).
            flag: Convergence flag (True if converged, False otherwise).
            task: The task name (e.g., 'eigh', 'tm').
            **kwargs: Additional context (L, W, realization_index, seed, etc.).
        """
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "task": task,
            "residual_norm": norm,
            "converged": flag,
            **kwargs
        }
        self._append_entry(entry)

    def log_convergence(self, metric: Dict[str, Any]):
        """
        Log convergence metrics for iterative solvers.

        Args:
            metric: Dictionary containing convergence details (iterations, history, etc.).
        """
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": "convergence_metric",
            "metric": metric
        }
        self._append_entry(entry)

    def _append_entry(self, entry: Dict[str, Any]):
        """Append a JSON line entry to the output file."""
        try:
            with open(self.output_path, "a") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            logger.error(f"Failed to write log entry: {e}")
            raise

def get_logger(output_path: Optional[str] = None) -> NumericalLogger:
    """Factory function to get a NumericalLogger instance."""
    return NumericalLogger(output_path)
