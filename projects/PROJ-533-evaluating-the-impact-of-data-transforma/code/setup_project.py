"""
Script to initialize the project directory structure for llmXive research pipeline.
Executes the exact command logic:
mkdir -p code/utils data/raw data/processed results/type1_error results/power results/aggregated results/checkpoints tests/unit tests/integration
"""
import os
from pathlib import Path

def main():
    # Define the relative paths to be created based on task T001 requirements
    base_dirs = [
        "code/utils",
        "data/raw",
        "data/processed",
        "results/type1_error",
        "results/power",
        "results/aggregated",
        "results/checkpoints",
        "tests/unit",
        "tests/integration"
    ]

    # Create directories
    for dir_path in base_dirs:
        full_path = Path(dir_path)
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {full_path.resolve()}")

    print("Project structure initialization complete.")

if __name__ == "__main__":
    main()