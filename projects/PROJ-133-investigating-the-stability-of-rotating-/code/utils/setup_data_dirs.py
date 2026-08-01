import os
import sys
from pathlib import Path

def create_project_structure(base_dir: Path) -> None:
    """
    Create the required directory structure for the project.
    
    This function ensures the existence of:
    - code/simulation, code/analysis, code/statistics, code/viz, code/utils
    - data/raw, data/processed, data/aggregated
    - tests/unit, tests/contract, tests/integration
    - docs
    
    Args:
        base_dir: The root directory of the project where structures will be created.
    """
    # Define the required directory paths relative to the base directory
    directories = [
        # Code subdirectories
        base_dir / "code" / "simulation",
        base_dir / "code" / "analysis",
        base_dir / "code" / "statistics",
        base_dir / "code" / "viz",
        base_dir / "code" / "utils",
        
        # Data subdirectories (specifically for T004)
        base_dir / "data" / "raw",
        base_dir / "data" / "processed",
        base_dir / "data" / "aggregated",
        
        # Test subdirectories
        base_dir / "tests" / "unit",
        base_dir / "tests" / "contract",
        base_dir / "tests" / "integration",
        
        # Documentation
        base_dir / "docs",
    ]
    
    # Create directories if they don't exist
    created_count = 0
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created directory: {directory}")
        else:
            print(f"Directory already exists: {directory}")
    
    print(f"Project structure setup complete. {created_count} directories created/verified.")

def main():
    """
    Entry point for the script. Creates the data directory structure.
    """
    # Determine the project root (parent of the 'code' directory)
    current_file = Path(__file__).resolve()
    code_dir = current_file.parent
    project_root = code_dir.parent
    
    print(f"Project root detected at: {project_root}")
    
    # Create the structure
    create_project_structure(project_root)
    
    # Verify the specific data directories required for T004
    data_base = project_root / "data"
    required_subdirs = ["raw", "processed", "aggregated"]
    
    for subdir in required_subdirs:
        path = data_base / subdir
        if path.exists() and path.is_dir():
            print(f"✓ Verified: {path}")
        else:
            print(f"✗ Missing: {path}")
            raise FileNotFoundError(f"Required directory {path} was not created.")

if __name__ == "__main__":
    main()