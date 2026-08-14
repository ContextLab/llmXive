import os
import sys
from pathlib import Path

def main():
    """Creates the project directory structure."""
    dirs = [
        "code/data_ingestion",
        "code/modeling",
        "code/reporting",
        "code/utils",
        "tests",
        "data/raw",
        "data/processed",
        "results",
        "logs",
        "docs"
    ]

    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path}")

if __name__ == "__main__":
    main()
