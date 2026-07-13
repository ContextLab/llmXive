"""Convenience script to generate correlation results.

The project’s quick‑start run‑book expects a script that, when executed,
produces ``data/analysis/correlation_results.csv``.  This file simply
forwards to the :pyfunc:`code.correlation_analysis.main` function.
"""

from __future__ import annotations

import logging
from pathlib import Path

# Import the main entry point from the correlation_analysis module.
from correlation_analysis import main as correlation_main

def _ensure_output_dir() -> None:
    """Make sure the output directory exists before the analysis runs."""
    out_dir = Path("data/analysis")
    out_dir.mkdir(parents=True, exist_ok=True)

def main() -> None:
    """Run the correlation analysis and guarantee the output directory exists."""
    logging.basicConfig(level=logging.INFO)
    _ensure_output_dir()
    correlation_main()

if __name__ == "__main__":  # pragma: no cover
    main()
