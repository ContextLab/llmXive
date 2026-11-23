"""
Script to execute T006: Simulated Injection Generation.
Runs the injection generation logic and ensures the output file is written.
"""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from src.data_loader import main

if __name__ == "__main__":
    print("Starting T006: Simulated Injection Generation...")
    exit_code = main()
    if exit_code == 0:
        print("T006 completed successfully.")
    else:
        print("T006 failed.")
    sys.exit(exit_code)