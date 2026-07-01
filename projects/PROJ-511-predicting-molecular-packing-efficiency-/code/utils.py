"""
Utility functions and constants for the molecular packing efficiency project.

This module provides:
- Reproducible seed fixing for random number generators.
- Centralized logging setup.
- Bondi van der Waals radii constants for packing calculations.
"""

import logging
import os
import random
import sys
from typing import Dict, Optional

import numpy as np

# ---------------------------------------------------------------------------
# Bondi Van der Waals Radii (Angstroms)
# Source: Bondi, A. J. Phys. Chem. 1964, 68, 441.
# Used for calculating molecular volumes and packing coefficients.
# ---------------------------------------------------------------------------
BONDI_RADII: Dict[str, float] = {
    "H": 1.20,
    "He": 1.40,
    "C": 1.70,
    "N": 1.55,
    "O": 1.52,
    "F": 1.47,
    "Ne": 1.54,
    "Si": 2.10,
    "P": 1.80,
    "S": 1.80,
    "Cl": 1.75,
    "Ar": 1.88,
    "As": 1.85,
    "Se": 1.90,
    "Br": 1.85,
    "Kr": 1.98,
    "Te": 2.06,
    "I": 1.98,
    "Xe": 2.16,
    # Add other common organic elements if needed
    "B": 1.92,
    "Li": 1.82,
    "Na": 2.27,
    "K": 2.75,
    "Mg": 1.73,
    "Ca": 2.31,
    "Fe": 2.00, # Approximate, varies by oxidation state
    "Zn": 1.39, # Metal coordination radii differ, using covalent approx if needed
}

# ---------------------------------------------------------------------------
# Reproducibility
# ---------------------------------------------------------------------------

def fix_seed(seed: int = 42) -> None:
    """
    Fix the random seed for reproducibility across numpy, random, and torch (if available).

    Args:
        seed: Integer seed value. Default is 42.
    """
    random.seed(seed)
    np.random.seed(seed)

    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        # Torch not installed; skip torch seeding
        pass

    # Ensure deterministic behavior in some operations if torch is available
    if "torch" in sys.modules:
        import torch
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    name: str = "molecular_packing"
) -> logging.Logger:
    """
    Configure and return a logger with console and optional file handlers.

    Args:
        level: Logging level (e.g., logging.INFO, logging.DEBUG).
        log_file: Optional path to a log file. If None, only console logging is used.
        name: Name of the logger.

    Returns:
        Configured logging.Logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    # Formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (optional)
    if log_file:
        # Ensure directory exists
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger