import os
import sys
from pathlib import Path

def create_directories():
    """
    Create the project directory structure as specified in T001.
    
    Directories created:
    - src/data, src/models, src/analysis
    - data/raw, data/processed, data/interim
    - tests/contract, tests/unit, tests/integration
    - docs
    """
    base_dir = Path(__file__).parent.parent
    
    directories = [
        "src/data",
        "src/models",
        "src/analysis",
        "data/raw",
        "data/processed",
        "data/interim",
        "tests/contract",
        "tests/unit",
        "tests/integration",
        "docs"
    ]
    
    created = []
    for d in directories:
        full_path = base_dir / d
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created.append(str(full_path))
        else:
            print(f"Directory already exists: {full_path}")
    
    if created:
        print(f"Created {len(created)} directories:")
        for d in created:
            print(f"  - {d}")
    else:
        print("All directories already exist.")
    
    return created

if __name__ == "__main__":
    create_directories()