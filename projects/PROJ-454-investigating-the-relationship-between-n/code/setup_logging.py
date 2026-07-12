"""
Script to initialize the logging infrastructure for the project.
This ensures log directories and CSV headers are created before any pipeline runs.
"""
import os
import sys
from pathlib import Path

# Add code directory to path
code_dir = Path(__file__).resolve().parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from utils.logging_config import initialize_project_logging

def main():
    print("Initializing logging infrastructure...")
    loggers = initialize_project_logging()
    print(f"Log directory: {code_dir.parent / 'logs'}")
    print("Loggers initialized:")
    for name, logger in loggers.items():
        print(f"  - {name}: {logger.level}")
    print("Logging infrastructure ready.")

if __name__ == "__main__":
    main()