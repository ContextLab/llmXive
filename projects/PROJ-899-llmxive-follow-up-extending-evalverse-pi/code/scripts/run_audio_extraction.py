"""
Script to run audio feature extraction (T013).
"""
import os
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data.extract_audio import main
from src.utils import setup_logging

def main_wrapper():
    setup_logging()
    main()

if __name__ == "__main__":
    main_wrapper()