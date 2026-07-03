"""
Runner script for T030: Generate scaling_plot.pdf with power-law fits and reliability notes.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Add code directory to path
code_dir = Path(__file__).parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from analysis.scaling_plot_generator import main

if __name__ == '__main__':
    sys.exit(main())
