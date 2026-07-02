import os
import sys
from pathlib import Path

def create_directories(base_path: Path) -> None:
    """Create the project directory structure."""
    # Root directories
    dirs = [
        "code",
        "data",
        "tests",
        "data/raw-fmri",
        "data/processed-fmri",
        "data/behavioral",
        "data/results",
        "code/data_download",
        "code/manipulation",
        "code/preprocess",
        "code/analysis",
        "code/visualization",
        "code/utils",
        "code/pipeline",
        "code/config",
        "tests/unit",
        "tests/integration",
        "tests/contract",
    ]

    for dir_path in dirs:
        full_path = base_path / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        # Create __init__.py in Python directories to make them packages
        if dir_path.startswith("code") or dir_path.startswith("tests"):
            init_file = full_path / "__init__.py"
            if not init_file.exists():
                init_file.write_text(f"# {dir_path} module\n")

def main():
    """Main entry point for setting up the project structure."""
    # Determine project root (assuming script is run from project root)
    base_path = Path.cwd()
    
    create_directories(base_path)
    print("Project directory structure created successfully.")

if __name__ == "__main__":
    main()
