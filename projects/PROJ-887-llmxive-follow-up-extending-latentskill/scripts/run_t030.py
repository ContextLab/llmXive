import os
import sys
from pathlib import Path

# Ensure the project root is in the path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.validation.linearity_check import main as linearity_main

def main():
    """
    Execution script for T030: Linearity Check.
    This script runs the linearity analysis and ensures the output is written to disk.
    """
    print("Running T030: Linearity Check...")
    try:
        linearity_main()
        print("T030 completed successfully.")
    except Exception as e:
        print(f"T030 failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
