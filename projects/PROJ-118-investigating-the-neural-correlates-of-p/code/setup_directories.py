import os
from pathlib import Path

def setup_directories(base_path: str = ".") -> None:
    """
    Create the required directory structure for the project with .gitkeep files.
    
    This implements T004: Setup `data/raw` and `data/processed` directory 
    structure with `.gitkeep` files.
    
    Args:
        base_path: Root directory where the project structure will be created.
                   Defaults to current working directory.
    """
    project_root = Path(base_path)
    
    # Define required directories
    directories = [
        "data/raw",
        "data/processed",
        "code",
        "tests",
        "results",
        "results/plots",
        "specs",
    ]
    
    for dir_path in directories:
        full_path = project_root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        
        # Create .gitkeep file to ensure directory is tracked by git
        gitkeep_path = full_path / ".gitkeep"
        if not gitkeep_path.exists():
            gitkeep_path.write_text(
                "# Keep this directory in git\n"
                "# This directory is part of the llmXive science pipeline\n"
            )
        
        print(f"Created directory: {full_path}")
        if not gitkeep_path.exists():
            print(f"  (Note: .gitkeep already existed)")
        else:
            print(f"  Created .gitkeep: {gitkeep_path}")

if __name__ == "__main__":
    setup_directories()
