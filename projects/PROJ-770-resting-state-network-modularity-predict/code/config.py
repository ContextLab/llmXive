"""
config.py
=========

Central configuration module for the Resting‑State Network Modularity project.

This file defines:
* Standardised data directories (raw, processed, results) as ``pathlib.Path`` objects.
* Hyper‑parameters that are shared across pipeline scripts, such as the default
  graph‑threshold percentage and the list of sensitivity‑analysis increments.

The module purposefully avoids any heavy logic – it only provides constants.
Scripts import the required names, e.g.::

    from config import THRESHOLD_PERCENT, SENSITIVITY_INCREMENTS
    from config import DATA_RAW_DIR, DATA_PROCESSED_DIR, DATA_RESULTS_DIR

The paths are relative to the project root; the ``llmxive_toolkit.paths`` helper
is not used here to keep the configuration import‑only and lightweight.
"""

from pathlib import Path
from typing import List

# ----------------------------------------------------------------------
# Data directory layout
# ----------------------------------------------------------------------
# These are the canonical locations used throughout the pipeline.  They are
# defined as ``Path`` objects so that downstream code can call ``mkdir`` or
# ``exists`` as needed.
DATA_ROOT_DIR: Path = Path.cwd()  # project root (assumed to be cwd at runtime)

DATA_RAW_DIR: Path = DATA_ROOT_DIR / "data" / "raw"
"""Directory for raw files downloaded from external sources (e.g., HCP NIfTI, CSV)."""

DATA_PROCESSED_DIR: Path = DATA_ROOT_DIR / "data" / "processed"
"""Directory for intermediate artefacts such as correlation matrices, cleaned behavioural CSVs, etc."""

DATA_RESULTS_DIR: Path = DATA_ROOT_DIR / "data" / "results"
"""Directory for final outputs (regression tables, summary CSVs, figures)."""

# ----------------------------------------------------------------------
# Hyper‑parameters
# ----------------------------------------------------------------------
# Default proportion of strongest positive edges to retain when thresholding
# functional connectivity matrices.  The value is expressed as a percentage
# (0 < THRESHOLD_PERCENT <= 100).  It matches the specification default of 10 %.
THRESHOLD_PERCENT: float = 10.0

# Sensitivity‑analysis thresholds: start, stop, step (inclusive start, exclusive stop)
# The quickstart/run‑book expects a range string like "10,30,5".  Providing the
# concrete list here makes it easy for downstream scripts to iterate.
SENSITIVITY_THRESHOLD_START: int = 10
SENSITIVITY_THRESHOLD_STOP: int = 31  # stop is exclusive; 30 % inclusive
SENSITIVITY_THRESHOLD_STEP: int = 5

# Helper list derived from the start/stop/step values.
SENSITIVITY_INCREMENTS: List[int] = list(
    range(SENSITIVITY_THRESHOLD_START, SENSITIVITY_THRESHOLD_STOP, SENSITIVITY_THRESHOLD_STEP)
)
"""List of threshold percentages used for the sensitivity analysis (e.g., [10, 15, 20, 25, 30])."""

# ----------------------------------------------------------------------
# Miscellaneous defaults
# ----------------------------------------------------------------------
# Number of subjects to sample when the download script is invoked without an
# explicit ``--sample-size`` flag.  This aligns with the specification's pilot
# cohort size.
DEFAULT_SAMPLE_SIZE: int = 200

__all__ = [
    "DATA_ROOT_DIR",
    "DATA_RAW_DIR",
    "DATA_PROCESSED_DIR",
    "DATA_RESULTS_DIR",
    "THRESHOLD_PERCENT",
    "SENSITIVITY_INCREMENTS",
    "SENSITIVITY_THRESHOLD_START",
    "SENSITIVITY_THRESHOLD_STOP",
    "SENSITIVITY_THRESHOLD_STEP",
    "DEFAULT_SAMPLE_SIZE",
]