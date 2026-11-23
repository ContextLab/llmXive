"""
Script to initialize linting and formatting tools for the project.

This script:
1. Creates configuration files for Ruff and Black
2. Provides instructions for running the tools
"""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from code.utils.lint_config import main as setup_linting_main

def main() -> int:
    """Run the linting setup."""
    return setup_linting_main()

if __name__ == "__main__":
    sys.exit(main())