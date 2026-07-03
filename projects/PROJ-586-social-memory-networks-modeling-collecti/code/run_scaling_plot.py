"""
Runner script for scaling plot generation (T030).

Executes the scaling plot generation to produce scaling_plot.pdf
with power-law fits and reliability notes.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Add code directory to path for imports
code_dir = Path(__file__).parent
sys.path.insert(0, str(code_dir))

from analysis.scaling_plot_generator import main as scaling_plot_main


def main() -> int:
    """Entry point for scaling plot generation runner."""
    return scaling_plot_main()


if __name__ == "__main__":
    sys.exit(main())