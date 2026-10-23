"""
window.py

Generate the deterministic window index required for the Möbius
autocorrelation pipeline.

This script is a thin wrapper around the ``window_index`` module,
which contains the actual implementation.  It uses the canonical
parameters specified in the project plan:

  * N = 10 000 000  (maximum index of the Möbius array)
  * interval lengths L ∈ {1000, 10000, 100000}
  * 100 non‑overlapping windows per length
  * seed = 20231017  (deterministic RNG)

The resulting CSV is written to ``data/processed/window_index.csv``
with the columns ``interval_start,interval_length,window_id``.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Helper from the llmxive toolkit for path handling.
from llmxive_toolkit import paths

# The core generator lives in ``window_index``; we import the
# public function that performs the work.
from window_index import generate_window_index

def main() -> None:
    """
    Entry point for the window‑index generation stage.

    It forwards the deterministic parameters to
    ``generate_window_index`` and writes the CSV to the location
    expected by downstream stages (``data/processed/window_index.csv``).
    """
    # Deterministic parameters as defined in the specification.
    N = 10_000_000
    L_VALUES = [1000, 10_000, 100_000]
    WINDOWS_PER_L = 100
    SEED = 20231017

    output_path: Path = paths.processed("window_index.csv")

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