"""
Script to execute T086: Archive all artifacts and logs.

This is a wrapper script to ensure the archive task can be run
independently from the command line.
"""
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.evaluation.archive_artifacts import main

if __name__ == "__main__":
    sys.exit(main())
