import os
from pathlib import Path

def create_directory_structure():
    """
    Creates the full directory structure required for the project.
    This includes data directories, results, state, contracts, logs, docs,
    and the source/test tree as specified in T004a.
    
    Creates .gitkeep files in all directories to ensure version control tracking.
    """
    # Define all required directories relative to the project root
    # Assuming this script runs from the project root or code/ directory
    project_root = Path(__file__).parent.parent
    
    directories = [
        # Data directories
        "data/raw",
        "data/processed",
        
        # Output and state directories
        "results",
        "state",
        
        # Configuration and contracts
        "contracts",
        
        # Logging and documentation
        "logs",
        "docs",
        
        # Source code structure
        "src",
        "src/data",
        "src/graphs",
        "src/metrics",
        "src/analysis",
        "src/utils",
        "src/data_ingestion",
        "src/constants",
        
        # Test structure
        "tests/unit",
        "tests/integration",
        "tests/contract",
    ]
    
    created_count = 0
    for dir_path in directories:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created directory: {full_path}")
        
        # Create .gitkeep file to ensure directory is tracked by git
        gitkeep_path = full_path / ".gitkeep"
        if not gitkeep_path.exists():
            gitkeep_path.touch()
            print(f"Created .gitkeep in: {full_path}")
    
    print(f"\nDirectory structure setup complete.")
    print(f"Created {created_count} new directories.")
    print(f"Added .gitkeep files to all directories.")
    
    return True

if __name__ == "__main__":
    create_directory_structure()
