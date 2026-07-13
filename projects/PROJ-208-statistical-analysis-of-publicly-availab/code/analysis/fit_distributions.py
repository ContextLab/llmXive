"""
Wrapper script to execute distribution fitting analysis.

This script serves as the entry point for T016, ensuring the
distribution_fitting module is executed correctly.
"""

import sys
from pathlib import Path

# Add the code directory to the path to allow imports
code_root = Path(__file__).parent.parent
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from analysis.distribution_fitting import main

if __name__ == '__main__':
    sys.exit(main())
