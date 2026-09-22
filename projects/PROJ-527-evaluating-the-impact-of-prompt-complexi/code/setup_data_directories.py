"""
Setup Data Directory Structure.

Creates the required directory hierarchy for raw, processed, and result data
to support the research pipeline.
"""

import os
from pathlib import Path

# Project root is assumed to be the parent of 'code/'
_PROJECT_ROOT = Path(__file__).resolve().parent.parent


def create_data_directories() -> None:
    """
    Create the standard data directory structure.

    Creates:
        - data/raw/           : For downloaded source data (e.g., HumanEval)
        - data/processed/     : For cleaned, transformed, and intermediate data
        - data/results/       : For final analysis outputs and CSV reports
    """
    data_base = _PROJECT_ROOT / "data"
    dirs = [
        data_base / "raw",
        data_base / "processed",
        data_base / "results",
    ]

    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        # Ensure the directory exists on disk
        if not d.exists():
            raise RuntimeError(f"Failed to create directory: {d}")

    print(f"Data directories created under: {data_base}")


def main() -> None:
    """Entry point for CLI execution."""
    create_data_directories()


if __name__ == "__main__":
    main()
