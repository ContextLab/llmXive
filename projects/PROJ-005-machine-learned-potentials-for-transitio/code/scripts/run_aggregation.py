"""
Script to run the ensemble result aggregation.

This script is the entry point for T023c. It loads the 5 model checkpoints,
generates predictions, aggregates them, and saves the ensemble variance.
"""

import sys
import logging
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.models.aggregate_ensemble import main

if __name__ == "__main__":
    main()
