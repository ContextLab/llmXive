"""
Entry point for generating the scaling plot (T030).
"""
import sys
from pathlib import Path

# Add code directory to path for imports
code_dir = Path(__file__).parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from analysis.scaling_plot_generator import main

if __name__ == "__main__":
    main()