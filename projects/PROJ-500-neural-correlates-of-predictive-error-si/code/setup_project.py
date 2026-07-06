"""
Project Initialization Script for PROJ-500-neural-correlates-of-predictive-error-si

This script creates the required directory structure and initializes
essential configuration files for the project.
"""
import os
from pathlib import Path


def main():
    """Create the project directory structure and essential files."""
    # Define the root directory (current working directory)
    root = Path.cwd()
    
    # Define required directories relative to root
    directories = [
        "src",
        "src/data",
        "src/utils",
        "src/analysis",
        "tests",
        "tests/unit",
        "tests/contract",
        "tests/integration",
        "contracts",
        "data",
        "data/raw",
        "data/processed",
        "data/interim",
        "analysis",
        "analysis/results",
        "logs",
        "figures",
        "docs",
        "specs",
    ]
    
    # Create directories
    created_dirs = []
    for dir_path in directories:
        full_path = root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(str(full_path))
        else:
            # Ensure it's actually a directory, not a file
            if not full_path.is_dir():
                raise RuntimeError(f"Path exists but is not a directory: {full_path}")
    
    # Create essential __init__.py files for Python packages
    package_dirs = [
        "src",
        "src/data",
        "src/utils",
        "src/analysis",
        "tests",
        "tests/unit",
        "tests/contract",
        "tests/integration",
    ]
    
    for pkg_dir in package_dirs:
        init_file = root / pkg_dir / "__init__.py"
        if not init_file.exists():
            init_file.write_text(f'"""Package for {pkg_dir}."""\n')
    
    # Create .gitkeep files in data directories to ensure they are tracked
    data_dirs = ["data/raw", "data/processed", "data/interim"]
    for data_dir in data_dirs:
        gitkeep = root / data_dir / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.write_text("# Keep this directory in git\n")
    
    # Create logs directory gitkeep
    logs_gitkeep = root / "logs" / ".gitkeep"
    if not logs_gitkeep.exists():
        logs_gitkeep.write_text("# Keep this directory in git\n")
    
    # Create figures directory gitkeep
    figures_gitkeep = root / "figures" / ".gitkeep"
    if not figures_gitkeep.exists():
        figures_gitkeep.write_text("# Keep this directory in git\n")
    
    # Print summary
    print(f"Project structure initialized at: {root}")
    print(f"Created {len(created_dirs)} directories")
    print(f"Created {len(package_dirs)} __init__.py files")
    print(f"Created {len(data_dirs) + 2} .gitkeep files")
    
    return True


if __name__ == "__main__":
    main()