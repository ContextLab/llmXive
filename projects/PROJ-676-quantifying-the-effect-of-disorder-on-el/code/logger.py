"""
Numerical stability logger for tracking residuals and convergence.
Implements FR-008 and Constitution Principle VI.
"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Callable
import logging

class NumericalLogger:
    """Logger for numerical stability metrics."""

    def __init__(self, output_path: str):
        """
        Initialize the logger.

        Args:
            output_path: Path to the JSON lines output file.
        """
        self.output_path = Path(output_path)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)

    def log_residual(self, norm: float, flag: bool) -> None:
        """
        Log a residual norm and convergence flag.

        Args:
            norm: The residual norm value.
            flag: Boolean indicating convergence status.
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "residual",
            "norm": norm,
            "flag": flag
        }
        self._write_entry(entry)

    def log_convergence(self, metric: Dict[str, Any]) -> None:
        """
        Log convergence metrics.

        Args:
            metric: Dictionary containing convergence data.
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "convergence",
            "data": metric
        }
        self._write_entry(entry)

    def _write_entry(self, entry: Dict[str, Any]) -> None:
        """
        Write a single entry to the JSON lines file.

        Args:
            entry: Dictionary to write.
        """
        with open(self.output_path, 'a') as f:
            f.write(json.dumps(entry) + '\n')
            f.flush()

_global_logger: Optional[NumericalLogger] = None

def get_logger(output_path: str = "data/metadata/residuals.json") -> NumericalLogger:
    """
    Get or create the global numerical logger instance.

    Args:
        output_path: Path to the output file.

    Returns:
        NumericalLogger instance.
    """
    global _global_logger
    if _global_logger is None:
        _global_logger = NumericalLogger(output_path)
    return _global_logger

def log_residual_decorator(func: Callable) -> Callable:
    """
    Decorator to log residuals for a function.

    Args:
        func: Function to wrap.

    Returns:
        Wrapped function.
    """
    def wrapper(*args, **kwargs):
        logger = get_logger()
        try:
            result = func(*args, **kwargs)
            # Assume function returns a residual norm or we compute it
            # This is a generic decorator; specific implementations should pass norm
            logger.log_convergence({"function": func.__name__, "status": "success"})
            return result
        except Exception as e:
            logger.log_residual(0.0, False)
            raise
    return wrapper

def log_convergence_decorator(func: Callable) -> Callable:
    """
    Decorator to log convergence for a function.

    Args:
        func: Function to wrap.

    Returns:
        Wrapped function.
    """
    def wrapper(*args, **kwargs):
        logger = get_logger()
        try:
            result = func(*args, **kwargs)
            logger.log_convergence({"function": func.__name__, "status": "success"})
            return result
        except Exception as e:
            logger.log_convergence({"function": func.__name__, "status": "failed", "error": str(e)})
            raise
    return wrapper

def inject_log_residual(func: Callable) -> Callable:
    """
    Decorator to inject logging calls into a function.
    This is a simplified version; real injection would require AST manipulation
    or explicit calls within the function body.

    Args:
        func: Function to wrap.

    Returns:
        Wrapped function.
    """
    def wrapper(*args, **kwargs):
        logger = get_logger()
        try:
            result = func(*args, **kwargs)
            logger.log_convergence({"function": func.__name__, "status": "success"})
            return result
        except Exception as e:
            logger.log_residual(0.0, False)
            raise
    return wrapper

def inject_log_convergence(func: Callable) -> Callable:
    """
    Decorator to inject convergence logging.

    Args:
        func: Function to wrap.

    Returns:
        Wrapped function.
    """
    return log_convergence_decorator(func)
