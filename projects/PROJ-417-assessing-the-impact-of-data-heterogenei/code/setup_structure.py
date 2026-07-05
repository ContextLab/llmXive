import os
from pathlib import Path

def main():
    """
    Creates the project directory structure as defined in plan.md.
    This script ensures all necessary folders for code, data, tests, and contracts exist.
    """
    project_root = Path(".")
    
    directories = [
        # Code modules
        "code/simulation",
        "code/analysis",
        "code/visualization",
        "code/reporting",
        "code/utils", # Added to support logging infrastructure referenced in API surface
        
        # Data directories
        "data/raw",
        "data/processed",
        "data/results",
        
        # Test directories
        "tests/unit",
        "tests/integration",
        
        # Contracts and specs (contracts usually live in specs or root, per tasks.md T004 it's in specs/.../contracts)
        # However, T001 explicitly lists 'contracts' as a top-level dir to mkdir. 
        # We will create the top-level 'contracts' as requested by T001.
        "contracts",
    ]

    created_count = 0
    for dir_path in directories:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created: {full_path}")
            created_count += 1
        else:
            print(f"Exists: {full_path}")

    print(f"Project structure setup complete. {created_count} new directories created.")
    return 0

if __name__ == "__main__":
    exit(main())
