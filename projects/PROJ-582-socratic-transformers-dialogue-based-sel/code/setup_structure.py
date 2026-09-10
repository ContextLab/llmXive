import os
import sys
from pathlib import Path

def create_directories():
    """Create the required project directory structure."""
    base_path = Path(__file__).parent / "projects" / "PROJ-582-socratic-transformers-dialogue-based-sel" / "code"
    
    # Define directories to create
    directories = [
        base_path / "src",
        base_path / "data" / "raw",
        base_path / "data" / "processed",
        base_path / "data" / "results",
        base_path / "tests",
    ]
    
    for dir_path in directories:
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path}")
    
    # Create .gitkeep files in data directories
    data_dirs = [
        base_path / "data" / "raw",
        base_path / "data" / "processed",
        base_path / "data" / "results",
    ]
    
    for data_dir in data_dirs:
        gitkeep_path = data_dir / ".gitkeep"
        gitkeep_path.write_text("# Placeholder to keep directory in version control\n")
        print(f"Created .gitkeep in: {data_dir}")

def verify_structure():
    """Verify that all required directories exist."""
    base_path = Path(__file__).parent / "projects" / "PROJ-582-socratic-transformers-dialogue-based-sel" / "code"
    
    required_dirs = [
        base_path / "src",
        base_path / "data" / "raw",
        base_path / "data" / "processed",
        base_path / "data" / "results",
        base_path / "tests",
    ]
    
    all_exist = all(dir_path.is_dir() for dir_path in required_dirs)
    
    # Check for .gitkeep files
    data_gitkeeps = [
        base_path / "data" / "raw" / ".gitkeep",
        base_path / "data" / "processed" / ".gitkeep",
        base_path / "data" / "results" / ".gitkeep",
    ]
    
    gitkeeps_exist = all(gitkeep_path.is_file() for gitkeep_path in data_gitkeeps)
    
    return all_exist and gitkeeps_exist

def main():
    """Main entry point for setup script."""
    print("Initializing project directory structure...")
    create_directories()
    
    if verify_structure():
        print("Project structure initialized successfully.")
        return 0
    else:
        print("Error: Failed to verify project structure.")
        return 1

if __name__ == "__main__":
    sys.exit(main())