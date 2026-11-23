"""
Script to run seed validation (Task T034b).
"""
import os
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.seed_validator import main
from src.utils import setup_logging

def main_wrapper():
    """Wrapper to ensure proper logging setup."""
    setup_logging(level=logging.INFO)
    exit_code = main()
    return exit_code

if __name__ == "__main__":
    exit_code = main_wrapper()
    sys.exit(exit_code)