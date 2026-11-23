"""
cap_properties.py

Enforce FR‑009 caps on intrinsic property values and log warnings for any
out‑of‑range values. This script is intended to be used both as a post‑hoc
validator after synthetic data generation and as an importable utility.

Usage (as a module):
    python -m src.data.cap_properties <path_to_synthetic_meta.csv>

The script will:
1. Load the CSV at the provided path.
2. Identify rows where ``dependency_depth`` exceeds the maximum allowed
   value of 5.
3. Cap those values to 5.
4. Write a warning line for each capped instance to
   ``data/logs/cap_warnings.log``.
5. Overwrite the original CSV with the corrected values.

The implementation relies only on the public API surface already present
in the repository (pandas, pathlib, argparse, and the ``llmxive_toolkit``
helpers for deterministic path handling and logging).
"""

import argparse
import csv
from pathlib import Path
import sys

import pandas as pd

from llmxive_toolkit import paths, get_logger

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
MAX_DEPENDENCY_DEPTH = 5
LOG_FILE = paths.data("logs", "cap_warnings.log")

# Ensure the log directory exists
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

log = get_logger(__name__, log_file=str(LOG_FILE))

# ----------------------------------------------------------------------
# Core functionality
# ----------------------------------------------------------------------
def enforce_caps(csv_path: Path) -> None:
    """
    Enforce the ``dependency_depth`` cap and log any adjustments.

    Parameters
    ----------
    csv_path: Path
        Path to the ``synthetic_meta.csv`` file.
    """
    if not csv_path.is_file():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    # Load the CSV; we keep the original column order intact.
    df = pd.read_csv(csv_path)

    if "dependency_depth" not in df.columns:
        raise KeyError(
            "Column 'dependency_depth' not found in CSV. "
            f"Columns present: {list(df.columns)}"
        )

    # Identify rows that exceed the cap.
    mask = df["dependency_depth"] > MAX_DEPENDENCY_DEPTH
    if mask.any():
        # Log a warning for each affected instance.
        for idx in df[mask].index:
            instance_id = df.at[idx, "instance_id"]
            original = df.at[idx, "dependency_depth"]
            log.warning(
                f"Instance {instance_id}: requested dependency_depth {original} "
                f"exceeds cap {MAX_DEPENDENCY_DEPTH}; capping to {MAX_DEPENDENCY_DEPTH}."
            )
            # Apply the cap.
            df.at[idx, "dependency_depth"] = MAX_DEPENDENCY_DEPTH

        # Overwrite the CSV with the corrected values.
        df.to_csv(csv_path, index=False)
    else:
        # No caps required – still write the CSV to preserve formatting.
        df.to_csv(csv_path, index=False)

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Enforce FR‑009 caps on synthetic property values and log warnings."
        )
    )
    parser.add_argument(
        "csv_path",
        type=Path,
        help="Path to the synthetic_meta.csv file to validate/cap.",
    )
    args = parser.parse_args(argv)

    try:
        enforce_caps(args.csv_path)
    except Exception as exc:
        log.error(f"Failed to enforce caps: {exc}")
        # Propagate the exception so the process exits with a non‑zero code.
        raise

if __name__ == "__main__":
    # When executed via ``python -m src.data.cap_properties`` the
    # ``__spec__`` attribute is set, and ``__package__`` resolves to
    # ``src.data``.  ``sys.argv[1:]`` contains the CLI arguments.
    main(sys.argv[1:])
