"""
Script to create the project directory structure for PROJ-227.
Implements Task T001.
"""
import os
from pathlib import Path

def main():
    project_root = Path("projects/PROJ-227-assessing-the-trade-offs-between-static-")
    
    # Define required directories based on T001 specification
    required_dirs = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "state",
        project_root / "code",
        project_root / "tests",
        # Additional standard directories for completeness
        project_root / "data" / "logs",
        project_root / "specs",
        project_root / "contracts",
        project_root / "figures",
    ]

    created_count = 0
    for dir_path in required_dirs:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory exists: {dir_path}")

    print(f"\nSetup complete. Created {created_count} new directories.")
    print(f"Project root: {project_root.resolve()}")

    # Verify structure
    print("\nVerifying structure:")
    for dir_path in required_dirs:
        if dir_path.exists():
            print(f"  [OK] {dir_path}")
        else:
            print(f"  [FAIL] {dir_path}")
            return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
