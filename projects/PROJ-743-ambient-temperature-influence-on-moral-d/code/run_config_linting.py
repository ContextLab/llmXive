"""
Runner script to execute linting configuration setup.
"""

import sys
from pathlib import Path

# Ensure the code directory is in the path for imports
code_dir = Path(__file__).parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from config_linting import main


if __name__ == "__main__":
    sys.exit(main())