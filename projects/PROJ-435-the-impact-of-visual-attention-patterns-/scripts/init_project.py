"""
Script to initialize the project directory structure.
This script creates the necessary folders for the llmXive pipeline.
"""
import os
import sys
import logging
from pathlib import Path

# Add the code directory to the path so we can import setup_data_structure
current_dir = Path(__file__).resolve().parent
root_dir = current_dir.parent
code_dir = root_dir / "code"
if code_dir.exists():
    sys.path.insert(0, str(code_dir))

from setup_data_structure import main

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    main()
