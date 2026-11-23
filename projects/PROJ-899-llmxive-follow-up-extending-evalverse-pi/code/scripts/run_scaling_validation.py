"""
Script to run the scaling validation gate (T021b).
This script validates the linear scaling assumption.
"""
import os
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.models.evaluate import main
from src.utils import setup_logging

def main_wrapper():
    """Wrapper to run the scaling validation main function."""
    setup_logging(level=logging.INFO)
    return main()

if __name__ == "__main__":
    sys.exit(main_wrapper())