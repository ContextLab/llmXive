import os
from pathlib import Path

def create_directories(base_path: Path) -> None:
    """
    Create the required directory structure for the project.
    
    Args:
        base_path: The root directory for the project structure.
    """
    # Define the directories to create
    directories = [
        base_path / "src",
        base_path / "data" / "raw",
        base_path / "data" / "processed",
        base_path / "data" / "results",
        base_path / "tests",
    ]
    
    # Create each directory if it doesn't exist
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {directory}")

def create_gitkeep_files(base_path: Path) -> None:
    """
    Create .gitkeep files in data directories to ensure they are tracked by git.
    
    Args:
        base_path: The root directory for the project structure.
    """
    # Define the data directories that need .gitkeep files
    data_dirs = [
        base_path / "data" / "raw",
        base_path / "data" / "processed",
        base_path / "data" / "results",
    ]
    
    # Create .gitkeep in each data directory
    for directory in data_dirs:
        gitkeep_path = directory / ".gitkeep"
        gitkeep_path.touch()
        print(f"Created .gitkeep in: {directory}")

def verify_structure(base_path: Path) -> bool:
    """
    Verify that all required directories and .gitkeep files exist.
    
    Args:
        base_path: The root directory for the project structure.
        
    Returns:
        bool: True if all required paths exist, False otherwise.
    """
    # Define the required paths
    required_dirs = [
        base_path / "src",
        base_path / "data" / "raw",
        base_path / "data" / "processed",
        base_path / "data" / "results",
        base_path / "tests",
    ]
    
    required_gitkeep_files = [
        base_path / "data" / "raw" / ".gitkeep",
        base_path / "data" / "processed" / ".gitkeep",
        base_path / "data" / "results" / ".gitkeep",
    ]
    
    # Check directories
    for directory in required_dirs:
        if not directory.is_dir():
            print(f"Missing directory: {directory}")
            return False
    
    # Check .gitkeep files
    for file_path in required_gitkeep_files:
        if not file_path.is_file():
            print(f"Missing .gitkeep file: {file_path}")
            return False
    
    return True

def main():
    """
    Main function to initialize the project directory structure.
    """
    # Define the base path for this project
    base_path = Path(__file__).parent
    
    print(f"Initializing project structure in: {base_path}")
    
    # Create directories
    create_directories(base_path)
    
    # Create .gitkeep files
    create_gitkeep_files(base_path)
    
    # Verify structure
    if verify_structure(base_path):
        print("Project structure verification: SUCCESS")
    else:
        print("Project structure verification: FAILED")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())