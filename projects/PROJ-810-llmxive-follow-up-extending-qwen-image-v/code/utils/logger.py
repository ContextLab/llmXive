"""
Project-wide logger and deterministic seed initializer.

This module sets deterministic seeds for ``random``, ``numpy`` and ``torch``,
writes the seed configuration to ``data/raw/logger_init.json`` and provides a
``get_logger`` function that forwards to the toolkit's logger implementation.
"""

import json
import logging
import random
from pathlib import Path

import numpy as np
import torch

# The llmxive_toolkit provides a convenient ``paths`` helper and a
# ``get_logger`` function that configures a logger with a standard format.
from llmxive_toolkit import paths, get_logger as _toolkit_get_logger

# ----------------------------------------------------------------------
# Deterministic seed configuration
# ----------------------------------------------------------------------
# A single fixed seed is used for all randomness sources to guarantee that
# the entire pipeline is reproducible. The same seed value is recorded in a
# JSON file for downstream provenance tracking.
_SEED = 42

def _initialize_seeds_and_record() -> None:
    """
    Initialise deterministic seeds for the standard libraries used in the
    project and write a JSON record to ``data/raw/logger_init.json``.
    """
    # Standard library ``random``
    random.seed(_SEED)

    # NumPy
    np.random.seed(_SEED)

    # PyTorch – set the global seed and enforce deterministic
    # algorithms.  ``torch.use_deterministic_algorithms`` raises an error
    # if a nondeterministic operation is attempted, which is desirable
    # for a reproducible scientific pipeline.
    torch.manual_seed(_SEED)
    torch.use_deterministic_algorithms(True)

    # Determine the absolute path for the output JSON file.
    # ``paths.root`` points to the project root directory.
    output_path: Path = paths.root / "data" / "raw" / "logger_init.json"

    # Ensure the parent directory exists.
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Record the seed configuration.
    seed_record = {
        "seed_random": _SEED,
        "seed_numpy": _SEED,
        "seed_torch": _SEED,
        "torch_deterministic_algorithms": True,
    }

    # Write the JSON file with pretty formatting.
    output_path.write_text(json.dumps(seed_record, indent=2))

# Run the initialisation at import time so that any subsequent import of
# this module (or a call to ``get_logger``) guarantees that the seeds are
# already fixed and the JSON file exists.
_initialize_seeds_and_record()

# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------
def get_logger(name: str) -> logging.Logger:
    """
    Return a project‑wide logger.

    This is a thin wrapper around :func:`llmxive_toolkit.get_logger` so that
    callers can import ``code.utils.logger.get_logger`` without needing to
    know about the toolkit directly.

    Parameters
    ----------
    name: str
        The name of the logger (typically ``__name__`` of the caller).

    Returns
    -------
    logging.Logger
        Configured logger instance.
    """
    return _toolkit_get_logger(name)
