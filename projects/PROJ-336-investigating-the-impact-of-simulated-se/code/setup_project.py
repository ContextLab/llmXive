"""
Project initialization script for llmXive research pipeline.
Creates the required directory structure and initial configuration files.
"""
import os
import sys
from pathlib import Path

def create_directory_structure(root_dir: Path) -> None:
    """
    Create the standard project directory structure.
    
    Args:
        root_dir: The root directory of the project.
    """
    directories = [
        "src",
        "src/utils",
        "src/data",
        "src/analysis",
        "src/viz",
        "tests",
        "tests/unit",
        "tests/integration",
        "data",
        "data/raw",
        "data/processed",
        "data/cache",
        "results",
        "results/figures",
        "results/stats",
        "specs",
        "logs",
    ]
    
    for dir_name in directories:
        dir_path = root_dir / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
        # Create .gitkeep to ensure empty directories are tracked
        (dir_path / ".gitkeep").touch()
    
    print(f"Directory structure created in: {root_dir}")

def create_initial_files(root_dir: Path) -> None:
    """
    Create initial configuration and placeholder files.
    
    Args:
        root_dir: The root directory of the project.
    """
    # Create requirements.txt
    requirements_path = root_dir / "requirements.txt"
    if not requirements_path.exists():
        requirements_path.write_text(
            "# Core dependencies\n"
            "nibabel>=5.0.0\n"
            "numpy>=1.24.0\n"
            "pandas>=2.0.0\n"
            "networkx>=3.1.0\n"
            "scikit-learn>=1.3.0\n"
            "scipy>=1.11.0\n"
            "matplotlib>=3.7.0\n"
            "seaborn>=0.12.0\n"
            "bids-validator>=1.12.0\n"
            "requests>=2.31.0\n"
            "fsl-afni-wrappers>=1.0.0\n"
        )
        print(f"Created: {requirements_path}")
    
    # Create .gitignore
    gitignore_path = root_dir / ".gitignore"
    if not gitignore_path.exists():
        gitignore_path.write_text(
            "# Python\n"
            "__pycache__/\n"
            "*.py[cod]\n"
            "*$py.class\n"
            ".pytest_cache/\n"
            ".coverage\n"
            "htmlcov/\n"
            "\n"
            "# Data\n"
            "data/raw/*\n"
            "!data/raw/.gitkeep\n"
            "*.nii.gz\n"
            "*.nii\n"
            "\n"
            "# Results\n"
            "results/*\n"
            "!results/.gitkeep\n"
            "\n"
            "# Logs\n"
            "logs/*\n"
            "!logs/.gitkeep\n"
            "\n"
            "# IDE\n"
            ".idea/\n"
            ".vscode/\n"
            "*.swp\n"
            "*.swo\n"
        )
        print(f"Created: {gitignore_path}")

def main() -> None:
    """Main entry point for project setup."""
    # Determine project root (parent of code directory)
    current_file = Path(__file__).resolve()
    code_dir = current_file.parent
    project_root = code_dir.parent if current_file.name == "setup_project.py" else code_dir
    
    print(f"Initializing project structure at: {project_root}")
    
    create_directory_structure(project_root)
    create_initial_files(project_root)
    
    print("Project setup complete.")

if __name__ == "__main__":
    main()
