import os
from pathlib import Path

def create_directories():
    """
    Create the project directory structure as defined in T001a.
    
    Directories:
    - src/data, src/models, src/analysis, src/cli, src/lib
    - data/raw, data/processed
    - results
    - tests/unit, tests/integration, tests/contract
    """
    base_path = Path(__file__).resolve().parent.parent
    dirs = [
        "src/data",
        "src/models",
        "src/analysis",
        "src/cli",
        "src/lib",
        "data/raw",
        "data/processed",
        "results",
        "tests/unit",
        "tests/integration",
        "tests/contract",
    ]
    
    created = []
    for d in dirs:
        full_path = base_path / d
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created.append(str(full_path))
        else:
            # Ensure it is actually a directory
            if not full_path.is_dir():
                raise NotADirectoryError(f"Path exists but is not a directory: {full_path}")
    
    if created:
        print(f"Created {len(created)} directories:")
        for p in created:
            print(f"  - {p}")
    else:
        print("All directories already exist.")
    
    return created

if __name__ == "__main__":
    create_directories()