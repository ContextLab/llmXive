import os
from pathlib import Path

def setup_data_directories():
    """
    Creates the necessary directory structure for the project.
    """
    dirs = [
        "code",
        "code/data",
        "code/analysis",
        "code/utils",
        "data",
        "data/raw",
        "data/processed/behavioral",
        "data/processed/centrality",
        "data/processed/regression",
        "data/processed/validation",
        "data/processed/logs",
        "data/processed/fmriprep",
        "data/artifacts",
        "tests",
        "tests/contract",
        "tests/integration",
        "tests/unit",
        "specs"
    ]

    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {d}")

if __name__ == "__main__":
    setup_data_directories()