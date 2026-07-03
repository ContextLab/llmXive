"""
Wrapper script to run scaling plot generation.
This is the entry point called by the pipeline for T030.
"""
import sys
from pathlib import Path

# Add code directory to path
code_dir = Path(__file__).parent
sys.path.insert(0, str(code_dir))

from analysis.scaling_plot_generator import main

if __name__ == '__main__':
    sys.exit(main())