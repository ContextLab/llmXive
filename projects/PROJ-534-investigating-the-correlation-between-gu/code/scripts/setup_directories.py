import os
import sys
from pathlib import Path

def main():
    """
    Initialize project directory structure for the Gut Microbiome & Cognitive Flexibility study.
    
    Creates the following directories relative to the project root:
    - src/ (with subdirectories for analysis, data, viz, power, sensitivity, utils)
    - tests/ (with subdirectories for unit, integration, contract)
    - data/raw, data/processed, data/results
    - logs/
    """
    # Determine project root (assuming script is at code/scripts/setup_directories.py)
    # The project root is two levels up from this script
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent.parent
    
    # Define relative paths to create
    directories = [
        "src/analysis",
        "src/data",
        "src/viz",
        "src/power",
        "src/sensitivity",
        "src/utils",
        "tests/unit",
        "tests/integration",
        "tests/contract",
        "data/raw",
        "data/processed",
        "data/results",
        "logs"
    ]
    
    created_count = 0
    for dir_path in directories:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path.relative_to(project_root)}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path.relative_to(project_root)}")
    
    print(f"\nDirectory setup complete. Created {created_count} new directories.")
    return 0

if __name__ == "__main__":
    sys.exit(main())