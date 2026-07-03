"""
Wrapper script to run the scaling plot generation.

This script ensures the output directory exists and invokes the
analysis.scaling_plot_generator module.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Add code directory to path if not already present
code_dir = Path(__file__).parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from analysis.scaling_plot_generator import main

if __name__ == '__main__':
    sys.exit(main())