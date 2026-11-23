"""
Script to run the speed constraint check (T025b).
"""
import sys
import logging
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.analysis.speed_constraint_check import main

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()