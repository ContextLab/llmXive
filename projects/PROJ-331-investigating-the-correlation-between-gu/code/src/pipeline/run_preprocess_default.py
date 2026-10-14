"""Run the preprocessing stage using the default raw data locations.

This script simply invokes :func:`code.src.pipeline.preprocess.run_preprocess`
without overriding any paths, causing the outputs to be written to the
canonical locations:

- ``data/processed/filtered_samples.parquet``
- ``data/processed/clr_abundances.parquet``

The script is intended to be executed as part of the T002 verification
step so that the required deliverable files exist on disk.
"""
from __future__ import annotations

import sys
from pathlib import Path

from code.src.pipeline import preprocess

def main() -> int:
    """Execute the preprocessing pipeline with default arguments."""
    # The default behaviour writes the two parquet files under
    # ``data/processed`` relative to the project root.
    try:
        summary = preprocess.run_preprocess()
    except Exception as exc:  # pragma: no cover
        print(f"Preprocessing failed: {exc}", file=sys.stderr)
        return 1

    # Log a short summary for the user.
    filtered_path = Path(summary["filtered_samples_path"])
    clr_path = Path(summary["clr_abundances_path"])
    print(f"Filtered samples written to: {filtered_path}")
    print(f"CLR abundances written to: {clr_path}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
