"""
Script to initialize the project directory structure for the
llmXive automated science pipeline: Assessing Uncertainty Quantification
Techniques for Materials Property Predictions.

This script creates the necessary directories as defined in task T001a.
"""

import os
import sys
from pathlib import Path

def main():
    """Create the required directory structure."""
    # Define the base project root (assuming this script is in code/ or code/setup/)
    # We look for 'data', 'code', 'tests', 'results' relative to the script's parent
    base_dir = Path(__file__).resolve().parent.parent

    # Define the directories to create relative to the base directory
    directories = [
        "data/raw",
        "data/processed",
        "code/models",
        "code/metrics",
        "code/stats",
        "code/utils",
        "results",
        "tests/unit",
        "tests/integration",
    ]

    created_count = 0
    existing_count = 0

    for dir_path in directories:
        full_path = base_dir / dir_path
        
        if full_path.exists():
            existing_count += 1
            print(f"Directory exists: {full_path}")
        else:
            full_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created directory: {full_path}")

    print(f"\nSetup complete. Created {created_count} directories. {existing_count} already existed.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
