"""
Tool to initialize the project directory structure.
This script creates all required directories for the llmXive pipeline.
"""
import os
from pathlib import Path

def main():
    root = Path(__file__).resolve().parent.parent.parent
    
    directories = [
        # Phase 1: Setup
        "src/services",
        "src/models",
        "src/utils",
        "src/data-models",
        "tests/unit",
        "tests/contract",
        "data/raw",
        "data/filtered",
        "data/scores",
        "outputs",
    ]

    created = []
    for dir_path in directories:
        full_path = root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created.append(str(full_path.relative_to(root)))
            print(f"Created: {full_path.relative_to(root)}")
        else:
            print(f"Exists: {full_path.relative_to(root)}")

    if not created:
        print("All directories already exist.")
    else:
        print(f"\nTotal new directories created: {len(created)}")

if __name__ == "__main__":
    main()
