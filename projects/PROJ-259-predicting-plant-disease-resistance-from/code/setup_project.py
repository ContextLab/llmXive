"""
Script to initialize the project directory structure for llmXive.
Creates the required folders: code/, data/, data/raw, data/processed,
artifacts/, artifacts/models, artifacts/reports, artifacts/figures, tests/.
"""
import os
from pathlib import Path

def main():
    root = Path(os.getcwd())
    # Define the required directories relative to the project root
    dirs = [
        "code",
        "data",
        "data/raw",
        "data/processed",
        "artifacts",
        "artifacts/models",
        "artifacts/reports",
        "artifacts/figures",
        "tests"
    ]

    created_count = 0
    for d in dirs:
        target_path = root / d
        if not target_path.exists():
            target_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {target_path}")
            created_count += 1
        else:
            print(f"Directory exists: {target_path}")

    print(f"Project structure initialization complete. {created_count} new directories created.")

if __name__ == "__main__":
    main()
