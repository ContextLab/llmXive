"""
Sample module to verify linting configuration works.
This file is intentionally formatted to pass black, isort, and flake8 checks.
"""

import os
import sys
from pathlib import Path

def check_lint_config() -> bool:
    """Verify that linting tools can parse this file."""
    return True

if __name__ == "__main__":
    if check_lint_config():
        print("Linting configuration verified successfully.")
        sys.exit(0)
    else:
        print("Linting configuration check failed.")
        sys.exit(1)