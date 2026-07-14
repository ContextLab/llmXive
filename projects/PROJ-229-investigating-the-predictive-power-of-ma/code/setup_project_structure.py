import os
from pathlib import Path

def create_project_structure():
    """
    Create the directory structure defined in T001.
    This function is idempotent (safe to run multiple times).
    """
    # Define directories relative to project root
    directories = [
        "code/data",
        "code/models",
        "code/utils",
        "tests/unit",
        "tests/integration",
        "data/raw",
        "data/processed",
        "data/results",
        "specs/001-phase-change-predictive-power/contracts",
        "logs"
    ]

    print("Creating project directory structure...")
    for dir_path in directories:
        path = Path(dir_path)
        path.mkdir(parents=True, exist_ok=True)
        print(f"  ✓ Created: {path}")
    
    # Create __init__.py files in Python packages
    python_packages = [
        "code",
        "code/data",
        "code/models",
        "code/utils",
        "tests",
        "tests/unit",
        "tests/integration"
    ]
    
    for pkg in python_packages:
        init_file = Path(pkg) / "__init__.py"
        if not init_file.exists():
            init_file.touch()
            print(f"  ✓ Created: {init_file}")

    print("\nProject structure initialization complete.")

if __name__ == "__main__":
    create_project_structure()
