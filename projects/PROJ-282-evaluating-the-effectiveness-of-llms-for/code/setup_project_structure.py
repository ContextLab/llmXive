"""
Project Structure Setup Script for llmXive Research Pipeline.
Creates the required directory hierarchy for the research project.
"""
import os
import sys
from pathlib import Path


def create_structure(project_root: Path = None) -> None:
    """
    Creates the standard project directory structure.
    
    Args:
        project_root: Optional path to project root. Defaults to current working directory.
    """
    if project_root is None:
        project_root = Path.cwd()
    
    # Define the required directory structure
    directories = [
        # Source code directories
        "src",
        "src/utils",
        "src/data",
        "src/models",
        "src/services",
        "src/analysis",
        
        # Test directories
        "tests",
        "tests/unit",
        "tests/integration",
        
        # Data directories
        "data",
        "data/raw",
        "data/processed",
        "data/results",
        "data/logs",
        "data/human_review",
        "data/canonical_patterns",
        
        # State and configuration
        "state",
        "state/projects",
        
        # Contracts and specs
        "contracts",
        
        # Scripts
        "scripts",
        
        # Figures and visualizations
        "figures",
    ]
    
    created_count = 0
    skipped_count = 0
    
    for dir_path in directories:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created directory: {full_path}")
        else:
            skipped_count += 1
            print(f"Directory already exists: {full_path}")
    
    print(f"\nSetup complete. Created {created_count} directories, skipped {skipped_count} existing.")


def main() -> None:
    """Main entry point for the script."""
    print("Initializing project structure for llmXive research pipeline...")
    create_structure()
    print("Project structure initialization complete.")


if __name__ == "__main__":
    main()