"""
Logging infrastructure for numerical residuals and convergence flags.

Implements Constitution Principle VI: Capture numerical residuals and convergence
flags for *every* eigenvalue problem to ensure reproducibility.

This module provides utilities to:
1. Configure a structured logger for the project.
2. Log eigenvalue solver residuals and convergence status to a JSON file.
3. Log warnings and errors to both console and file.
"""

import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from code.config import get_config


# Singleton logger instance
_logger: Optional[logging.Logger] = None
_handler_initialized: bool = False


def get_logger(name: str = "llmXive.research") -> logging.Logger:
    """
    Retrieve or initialize the project logger.

    Args:
        name: Logger name. Defaults to 'llmXive.research'.

    Returns:
        Configured logging.Logger instance.
    """
    global _logger, _handler_initialized

    if _logger is None:
        _logger = logging.getLogger(name)
        _logger.setLevel(logging.DEBUG)

        if not _handler_initialized:
            config = get_config()
            log_dir = Path(config.DATA_DIR) / "metadata"
            log_dir.mkdir(parents=True, exist_ok=True)

            log_file = log_dir / "numerical_residuals.log"

            # File handler for structured JSON logs
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(file_formatter)

            # Console handler for immediate feedback
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_formatter = logging.Formatter('%(levelname)s: %(message)s')
            console_handler.setFormatter(console_formatter)

            _logger.addHandler(file_handler)
            _logger.addHandler(console_handler)
            _handler_initialized = True

    return _logger


def log_eigenvalue_residual(
    system_params: Dict[str, Any],
    eigenvalues: List[float],
    eigenvectors: List[Any],
    residuals: List[float],
    converged: List[bool],
    solver_name: str = "scipy.linalg.eigh",
    timestamp: Optional[str] = None
) -> None:
    """
    Log the residuals and convergence status for a single eigenvalue problem.

    This function captures the numerical health of the solver for every
    disorder realization, satisfying Constitution Principle VI.

    Args:
        system_params: Dictionary containing system parameters (W, L, realization_index, seed).
        eigenvalues: List of computed eigenvalues.
        eigenvectors: List of computed eigenvectors (optional, used for context).
        residuals: List of residual norms for each eigenpair.
        converged: List of booleans indicating convergence for each eigenpair.
        solver_name: Name of the solver used (e.g., 'scipy.linalg.eigh').
        timestamp: Optional ISO timestamp. If None, current time is used.
    """
    logger = get_logger()

    if timestamp is None:
        timestamp = datetime.utcnow().isoformat()

    # Prepare the log entry
    entry = {
        "timestamp": timestamp,
        "solver": solver_name,
        "system": system_params,
        "summary": {
            "total_eigenpairs": len(eigenvalues),
            "converged_count": sum(1 for c in converged if c),
            "max_residual": max(residuals) if residuals else 0.0,
            "mean_residual": sum(residuals) / len(residuals) if residuals else 0.0,
            "all_converged": all(converged)
        },
        "details": []
    }

    # Log individual details only if there are issues or for sampling
    # To keep log size manageable, we only log full details if any failed to converge
    # or if the max residual exceeds a threshold (e.g., 1e-6)
    threshold = 1e-6
    if not all(converged) or any(r > threshold for r in residuals):
        for i, (eig, res, conv) in enumerate(zip(eigenvalues, residuals, converged)):
            entry["details"].append({
                "index": i,
                "eigenvalue": float(eig),
                "residual": float(res),
                "converged": conv
            })
    else:
        # Log a summary entry without details for successful runs
        entry["details"] = None

    logger.debug(f"Eigenvalue solve: W={system_params.get('W')}, L={system_params.get('L')}, "
                 f"realization={system_params.get('realization_index')}, "
                 f"all_converged={entry['summary']['all_converged']}")

    # We also append to a JSON file for easy programmatic analysis later
    _append_to_residuals_json(entry)


def _append_to_residuals_json(entry: Dict[str, Any]) -> None:
    """
    Append a log entry to the persistent JSON file for residuals.

    Args:
        entry: The log entry dictionary.
    """
    config = get_config()
    residuals_file = Path(config.DATA_DIR) / "metadata" / "residuals.json"

    # Ensure directory exists
    residuals_file.parent.mkdir(parents=True, exist_ok=True)

    # Read existing data if file exists
    data = []
    if residuals_file.exists():
        try:
            with open(residuals_file, 'r') as f:
                data = json.load(f)
        except json.JSONDecodeError:
            # If corrupted, start fresh but log a warning
            logger = get_logger()
            logger.warning(f"Residuals file {residuals_file} is corrupted. Overwriting.")
            data = []

    data.append(entry)

    # Write back
    with open(residuals_file, 'w') as f:
        json.dump(data, f, indent=2)


def log_numerical_warning(message: str, context: Optional[Dict[str, Any]] = None) -> None:
    """
    Log a specific numerical warning with context.

    Args:
        message: Warning message.
        context: Optional dictionary of context variables.
    """
    logger = get_logger()
    full_message = f"{message}"
    if context:
        full_message += f" | Context: {context}"
    logger.warning(full_message)


def log_numerical_error(message: str, context: Optional[Dict[str, Any]] = None) -> None:
    """
    Log a specific numerical error with context.

    Args:
        message: Error message.
        context: Optional dictionary of context variables.
    """
    logger = get_logger()
    full_message = f"{message}"
    if context:
        full_message += f" | Context: {context}"
    logger.error(full_message)
