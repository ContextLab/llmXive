import os
from pathlib import Path

def create_structure():
    """
    Creates the directory structure for the project.
    This script is the implementation of T001a and T001b.
    """
    base_dir = Path("projects/PROJ-558-consciousness-bootstrapping-self-aware-a")
    
    # Define directories as per task T001a
    dirs = [
        "data/raw",
        "data/processed",
        "code",
        "code/models",
        "code/training",
        "code/evaluation",
        "code/analysis",
        "code/utils",
        "tests",
        "artifacts",
        "artifacts/checkpoints",
        "artifacts/reports",
    ]
    
    created_count = 0
    for d in dirs:
        target = base_dir / d
        if not target.exists():
            target.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created directory: {target}")
        else:
            print(f"Directory exists: {target}")
    
    # Define __init__.py files as per task T001b
    init_files = [
        "code/__init__.py",
        "code/models/__init__.py",
        "code/training/__init__.py",
        "code/evaluation/__init__.py",
        "code/analysis/__init__.py",
        "code/utils/__init__.py",
    ]
    
    init_created = 0
    for f in init_files:
        target = base_dir / f
        if not target.exists():
            target.write_text("# Package initialization\n")
            init_created += 1
            print(f"Created file: {target}")
        else:
            print(f"File exists: {target}")
    
    print(f"\nSummary: Created {created_count} directories and {init_created} __init__.py files.")
    return True

if __name__ == "__main__":
    create_structure()
