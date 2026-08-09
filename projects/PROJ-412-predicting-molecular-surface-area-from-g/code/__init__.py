"""
llmXive - Automated Science Pipeline
Project: Predicting Molecular Surface Area from Graph Convolutional Networks
"""
import os
import sys
from pathlib import Path

# Ensure project root is in path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import core utilities
from code.utils.logging import setup_logging, get_logger
from code.utils.config import get_project_root, get_data_dir, get_results_dir

__version__ = "0.1.0"
__author__ = "llmXive Research Team"

def initialize():
    """Initialize the project environment."""
    logger = setup_logging()
    logger.info(f"Initializing llmXive pipeline v{__version__}")
    logger.info(f"Project root: {get_project_root()}")
    return True

if __name__ == "__main__":
    initialize()