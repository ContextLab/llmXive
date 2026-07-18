import os
import sys
from pathlib import Path

def setup_directories():
    """
    Creates the required project directory structure.
    Directories created:
      - src/, tests/
      - data/raw, data/processed, data/splits
      - results
      - contracts/
      - .github/workflows/
    """
    base_dir = Path(__file__).resolve().parent.parent
    
    # Define relative paths to create
    dirs = [
        "src",
        "tests",
        "data/raw",
        "data/processed",
        "data/splits",
        "results",
        "contracts",
        ".github/workflows"
    ]

    created_count = 0
    for rel_path in dirs:
        target = base_dir / rel_path
        if not target.exists():
            target.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {target}")
            created_count += 1
        else:
            print(f"Directory exists: {target}")
    
    # Create .gitkeep files in data directories to ensure they are tracked by git
    data_dirs = ["data/raw", "data/processed", "data/splits"]
    for rel_path in data_dirs:
        target = base_dir / rel_path / ".gitkeep"
        if not target.exists():
            target.touch()
            print(f"Created .gitkeep: {target}")

    # Create .gitkeep in results
    results_dir = base_dir / "results" / ".gitkeep"
    if not results_dir.exists():
        results_dir.touch()
        print(f"Created .gitkeep: {results_dir}")

    # Create .gitkeep in contracts
    contracts_dir = base_dir / "contracts" / ".gitkeep"
    if not contracts_dir.exists():
        contracts_dir.touch()
        print(f"Created .gitkeep: {contracts_dir}")

    print(f"\nSetup complete. Created {created_count} new directories.")
    return True

if __name__ == "__main__":
    setup_directories()
