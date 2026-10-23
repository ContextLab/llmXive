"""
code/window.py

Generate the deterministic window index required for the Möbius
autocorrelation pipeline and write it to the correct location
``data/processed/window_index.csv``.

The implementation mirrors the logic in ``code/window_index.py`` but
uses the project's ``paths`` helper to ensure the file is placed
under the ``data`` top‑level folder (as required by the specification
and the verification tests).
"""

from __future__ import annotations

import sys
from pathlib import Path

# Toolkit helper for deterministic project‑relative paths.
from llmxive_toolkit import paths

# Core generator lives in ``window_index``; we import the public
# function that performs the work.
from window_index import generate_window_index

def main() -> None:
    """
    Entry point for the window‑index generation stage.

    It forwards the deterministic parameters to ``generate_window_index``
    and writes the CSV to the location expected by downstream stages:
    ``data/processed/window_index.csv``.
    """
    # Deterministic parameters as defined in the specification.
    N = 10_000_000
    L_VALUES = [1000, 10_000, 100_000]
    WINDOWS_PER_L = 100
    SEED = 20231017

    # Correct output location – under the ``data`` top‑level folder.
    output_path: Path = paths.data("processed", "window_index.csv")

    generate_window_index(
        N=N,
        L_values=L_VALUES,
        windows_per_L=WINDOWS_PER_L,
        seed=SEED,
        output_path=output_path,
    )

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        # Any unexpected error should be visible to the orchestrator.
        print(f"[ERROR] Window index generation failed: {exc}", file=sys.stderr)
        raise
