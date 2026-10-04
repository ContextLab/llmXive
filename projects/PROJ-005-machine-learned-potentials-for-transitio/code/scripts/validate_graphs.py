"""
Script to validate generated graphs against the dataset schema.

This script serves as the entry point for the validation task T018.
It ensures that the graphs.parquet file conforms to the defined schema
before proceeding to downstream tasks like splitting or training.
"""
import sys
import logging
from pathlib import Path

# Add the project root to the path if not already present
# Assuming this script is at code/scripts/validate_graphs.py
# We need to import from code.src.data.validate_graphs
# The import path in the API surface is: from src.data.validate_graphs import main
# So we need to ensure 'code' is in sys.path or we are running from 'code'

# Adjust path to allow importing from code.src
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent  # code/

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.data.validate_graphs import main

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()