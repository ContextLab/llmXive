import os
import sys
from pathlib import Path
import logging

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from model_report import main
from config import ensure_directories
from utils import setup_logging

def main_entry():
    """
    Entry point for running the model report generation.
    """
    setup_logging(level=logging.INFO)
    ensure_directories([
        project_root / "data" / "results"
    ])
    return main()

if __name__ == "__main__":
    main_entry()