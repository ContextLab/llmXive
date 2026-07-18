import os
from pathlib import Path

def create_directory_structure(project_root: str) -> None:
    """
    Creates the required directory structure for the project's data and results.
    
    This function implements T004: Setup `data/` (raw, processed) and `results/` directory structure.
    It also ensures the `state/` and `logs/` directories exist as per the project plan.
    
    Args:
        project_root: The absolute or relative path to the project root directory.
    """
    root = Path(project_root)
    
    # Define the directory structure relative to the project root
    # Based on T001 and T004 requirements
    directories = [
        root / "data" / "raw",
        root / "data" / "processed",
        root / "results",
        root / "state",
        root / "logs",
        root / "docs",
        root / "contracts",
    ]
    
    created_count = 0
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {directory}")
            created_count += 1
        else:
            # Ensure subdirectories exist even if parent exists
            if not (directory / ".gitkeep").exists():
                # Create a .gitkeep file to ensure the directory is tracked in git
                # This is a common practice for empty directories in git
                (directory / ".gitkeep").touch()
            print(f"Directory already exists: {directory}")
    
    print(f"Directory setup complete. Created {created_count} new directories.")

if __name__ == "__main__":
    # Default to current directory if no argument provided
    import sys
    target_root = sys.argv[1] if len(sys.argv) > 1 else "."
    create_directory_structure(target_root)
    print(f"Data directory structure initialized at: {Path(target_root).resolve()}")