"""
Project Configuration Module
----------------------------

This module centralises configuration constants, path helpers and CLI
argument parsing for the llmXive follow‑up project.  It is deliberately
lightweight and avoids external dependencies beyond the standard
library and the llmxive_toolkit utilities that are already provided by
the execution environment.

The implementation is sufficient for the current set of tasks and
satisfies the import expectations of all existing scripts and tests.
"""

import argparse
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from llmxive_toolkit import paths, get_logger

# ----------------------------------------------------------------------
# Logger
# ----------------------------------------------------------------------
log = get_logger(__name__)

# ----------------------------------------------------------------------
# Directory name constants (used with `get_path`)
# ----------------------------------------------------------------------
# These constants are imported by many modules (e.g. download.py,
# curate.py, main.py).  They represent the top‑level sub‑folders under
# the project root.
DATA_RAW = "raw"
DATA_CURATED = "curated"
DATA_RESULTS = "results"

# ----------------------------------------------------------------------
# Core configuration values (derived from the specification)
# ----------------------------------------------------------------------
# Values that were originally defined in task T002.  They are kept here
# so that downstream code can import them directly.
HARD_INSTANCE_PERCENTILE: float = 0.20          # Bottom 20 % of coverage
COVERAGE_COLUMN_NAME: str = "initial_coverage"
SWEEP_SAMPLE_SIZE: Optional[int] = None        # Deferred; resolved at runtime
SWEEP_SEED: int = 42
DEFAULT_TURN_LIMIT: int = 3
MIN_SYNTHETIC_ISSUES: int = 50
VALIDATION_SAMPLE_SIZE: int = 10
TIE_THRESHOLD: float = 0.50
MAX_RUNTIME_HOURS: float = 6.0
SWEEP_STABILITY_THRESHOLD: float = 0.05
MODEL_PRECISION: str = "-bit"

# Compatibility alias used by `code/main.py`
MAX_EXECUTION_HOURS: float = MAX_RUNTIME_HOURS

# ----------------------------------------------------------------------
# Helper: resolve deferred configuration values
# ----------------------------------------------------------------------
def _create_parser() -> argparse.ArgumentParser:
    """Create the argument parser for CLI overrides."""
    parser = argparse.ArgumentParser(
        description="Resolve deferred configuration values for llmXive."
    )
    parser.add_argument(
        "--sweep-sample-size",
        type=int,
        help="Number of issues to sample for the sensitivity sweep."
    )
    parser.add_argument(
        "--max-hours",
        type=float,
        default=MAX_RUNTIME_HOURS,
        help="Maximum allowed execution time in hours."
    )
    return parser

def resolve_deferred_config(args: Optional[argparse.Namespace] = None) -> Dict[str, Any]:
    """
    Resolve configuration values that are marked as *deferred*.
    Values can be supplied via command‑line arguments or environment
    variables.  The returned dictionary contains only the overrides.
    """
    if args is None:
        parser = _create_parser()
        args = parser.parse_args()

    overrides: Dict[str, Any] = {}

    if args.sweep_sample_size is not None:
        overrides["SWEEP_SAMPLE_SIZE"] = args.sweep_sample_size
    elif "SWEEP_SAMPLE_SIZE" in os.environ:
        try:
            overrides["SWEEP_SAMPLE_SIZE"] = int(os.getenv("SWEEP_SAMPLE_SIZE"))
        except ValueError:
            log.warning("Environment variable SWEEP_SAMPLE_SIZE is not an integer; ignoring.")

    # Example of additional deferred parameters could be added here.

    return overrides

# ----------------------------------------------------------------------
# Path helper
# ----------------------------------------------------------------------
def get_path(*parts: str) -> Path:
    """
    Resolve a path relative to the project root.

    The function mirrors the behaviour of the original `paths` helper but
    works with arbitrary sub‑folders.  It also ensures that the target
    directory exists (creating it if necessary).

    Example:
        get_path(DATA_RAW, "swe_explore_raw.jsonl")
    """
    # Determine the project root (two levels up from this file)
    project_root = Path(__file__).resolve().parent.parent
    target = project_root.joinpath(*parts)

    # If the target looks like a file (has an extension) we only ensure the
    # parent directory exists.
    if target.suffix:
        target.parent.mkdir(parents=True, exist_ok=True)
    else:
        target.mkdir(parents=True, exist_ok=True)

    return target

# ----------------------------------------------------------------------
# Configuration summary (useful for logging / debugging)
# ----------------------------------------------------------------------
def get_config_summary() -> Dict[str, Any]:
    """
    Return a dictionary summarising the current configuration.
    This is used by many scripts for diagnostic output.
    """
    summary: Dict[str, Any] = {
        "paths": {
            "raw": str(get_path(DATA_RAW)),
            "curated": str(get_path(DATA_CURATED)),
            "results": str(get_path(DATA_RESULTS)),
            "code": str(paths.code()),
            "tests": str(paths.tests()),
            "specs": str(Path(__file__).resolve().parent.parent.parent / "specs"),
        },
        "constants": {
            "HARD_INSTANCE_PERCENTILE": HARD_INSTANCE_PERCENTILE,
            "COVERAGE_COLUMN_NAME": COVERAGE_COLUMN_NAME,
            "SWEEP_SEED": SWEEP_SEED,
            "DEFAULT_TURN_LIMIT": DEFAULT_TURN_LIMIT,
            "MIN_SYNTHETIC_ISSUES": MIN_SYNTHETIC_ISSUES,
            "VALIDATION_SAMPLE_SIZE": VALIDATION_SAMPLE_SIZE,
            "TIE_THRESHOLD": TIE_THRESHOLD,
            "MAX_RUNTIME_HOURS": MAX_RUNTIME_HOURS,
            "SWEEP_STABILITY_THRESHOLD": SWEEP_STABILITY_THRESHOLD,
            "MODEL_PRECISION": MODEL_PRECISION,
        },
    }
    return summary

# ----------------------------------------------------------------------
# Convenience: ensure the required directory tree exists
# ----------------------------------------------------------------------
def ensure_directories() -> None:
    """
    Create all directories required by the project.  This function is
    called by various entry points (e.g. the quick‑start script) to make
    sure the filesystem layout is present before any I/O occurs.
    """
    required_dirs: List[Path] = [
        get_path("code"),
        get_path(DATA_RAW),
        get_path(DATA_CURATED),
        get_path(DATA_RESULTS),
        get_path("tests", "unit"),
        get_path("tests", "integration"),
        get_path("tests", "contract"),
        # Specification contracts directory
        Path(__file__).resolve().parent.parent.parent
        / "specs"
        / "001-llmxive-follow-up-extending-swe-explore"
        / "contracts",
    ]

    for d in required_dirs:
        if not d.exists():
            log.info(f"Creating required directory: {d}")
            d.mkdir(parents=True, exist_ok=True)
        else:
            log.debug(f"Directory already exists: {d}")

# When the module is imported, we proactively ensure the layout exists.
# This mirrors the behaviour expected by the quick‑start guide.
try:
    ensure_directories()
except Exception as exc:
    log.error(f"Failed to ensure project directories on import: {exc}")