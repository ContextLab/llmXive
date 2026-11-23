"""
Project setup script for PROJ-030-predicting-crystal-structures-from-molec.
Creates the required directory structure and placeholder files.
"""
import os
import sys
from pathlib import Path
from typing import Dict, Any

def ensure_directory(path: Path) -> None:
    """Ensure a directory exists, creating it if necessary."""
    path.mkdir(parents=True, exist_ok=True)

def create_placeholder_file(path: Path, content: str = "") -> None:
    """Create a placeholder file with optional initial content."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)

def main() -> None:
    """Create the project structure."""
    project_root = Path(__file__).resolve().parent.parent
    
    # Define directory structure
    directories = [
        project_root / "code",
        project_root / "code" / "ingestion",
        project_root / "code" / "modeling",
        project_root / "code" / "analysis",
        project_root / "code" / "utils",
        project_root / "data",
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "data" / "results",
        project_root / "data" / "validation",
        project_root / "data" / "models",
        project_root / "data" / "processing",
        project_root / "logs",
        project_root / "tests",
        project_root / "tests" / "unit",
        project_root / "tests" / "integration",
        project_root / "specs",
        project_root / "figures",
    ]
    
    # Create directories
    for directory in directories:
        ensure_directory(directory)
        print(f"Created directory: {directory}")
    
    # Create placeholder files
    placeholder_files = {
        project_root / "data" / ".gitkeep": "",
        project_root / "logs" / ".gitkeep": "",
        project_root / "figures" / ".gitkeep": "",
        project_root / "code" / "__init__.py": "",
        project_root / "tests" / "__init__.py": "",
        project_root / "specs" / "001-predict-crystal-structures" / "spec.md": "",
    }
    
    for path, content in placeholder_files.items():
        create_placeholder_file(path, content)
        print(f"Created file: {path}")
    
    print("Project structure created successfully.")

if __name__ == "__main__":
    main()