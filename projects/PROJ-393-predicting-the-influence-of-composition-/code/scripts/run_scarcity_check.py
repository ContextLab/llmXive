"""
Script to run the Scarcity Check (T028b).

This script should be executed after T027 (preprocess_pipeline) completes.
It verifies the dataset size and triggers T046 if N < 50.
"""
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.preprocessing.scarcity_checker import main

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()