import os
import sys
from pathlib import Path

def create_directories():
    """
    Create the required project directory structure.
    This satisfies T004 (code/ subdirectories) and T007 (data/ and tests/ directories).
    """
    root = Path(__file__).resolve().parents[2]
    
    # Define all required directories based on T001, T004, T007
    directories = [
        # Code structure (T004)
        root / "code" / "simulation",
        root / "code" / "models",
        root / "code" / "metrics",
        root / "code" / "validation",
        root / "code" / "plots",
        root / "code" / "scripts",
        
        # Data structure (T007)
        root / "data" / "raw",
        root / "data" / "simulated",
        root / "data" / "results",
        
        # Tests structure (T001)
        root / "tests" / "unit",
        root / "tests" / "integration",
        
        # Docs structure (T001)
        root / "docs" / "paper",
    ]

    created_count = 0
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {directory}")
            created_count += 1
        else:
            print(f"Directory already exists: {directory}")

    # Create .gitkeep files in data directories to ensure they are tracked by git (T007)
    data_dirs = [
        root / "data" / "raw",
        root / "data" / "simulated",
        root / "data" / "results",
    ]
    
    for data_dir in data_dirs:
        gitkeep_path = data_dir / ".gitkeep"
        if not gitkeep_path.exists():
            gitkeep_path.touch()
            print(f"Created .gitkeep in: {data_dir}")

    print(f"\nProject structure setup complete. Created {created_count} new directories.")
    return True

def main():
    """Entry point for CLI execution."""
    print("Setting up project directory structure...")
    success = create_directories()
    if success:
        print("Success.")
        sys.exit(0)
    else:
        print("Failed to set up directories.")
        sys.exit(1)

if __name__ == "__main__":
    main()
