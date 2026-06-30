"""
Script to initialize the project directory structure for the llmXive research pipeline.

This script creates the required directories for data storage, code organization,
testing, results, and logging as specified in the project plan.

Directories created:
- data/raw: For raw, unprocessed external data
- data/processed: For cleaned and transformed data
- code: For source code modules
- tests: For test suites
- results: For final outputs and reports
- logs: For application logs
- contracts: For schema definitions (created in Phase 2, but directory created here for completeness)
"""

import os
import sys


def create_directory_structure(base_path: str = ".") -> None:
    """
    Create the required directory structure relative to the base path.
    
    Args:
        base_path: Root directory path. Defaults to current directory.
    """
    directories = [
        "data/raw",
        "data/processed",
        "code",
        "tests",
        "results",
        "logs",
        "contracts",
    ]
    
    created_count = 0
    skipped_count = 0
    
    for dir_path in directories:
        full_path = os.path.join(base_path, dir_path)
        if not os.path.exists(full_path):
            os.makedirs(full_path, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")
            skipped_count += 1
    
    print(f"\nSummary: {created_count} directories created, {skipped_count} already existed.")


if __name__ == "__main__":
    create_directory_structure()
