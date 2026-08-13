import os
from pathlib import Path

def create_directories():
    """
    Create the project directory structure as defined in the implementation plan.
    Creates: src/, tests/, data/, output/, and subdirectories for data/raw and data/processed.
    """
    base_dir = Path(__file__).parent.parent
    
    directories = [
        "src",
        "src/analysis",
        "src/data",
        "src/utils",
        "tests",
        "tests/unit",
        "tests/integration",
        "data",
        "data/raw",
        "data/processed",
        "output",
        "output/temporal_profiles",
        "specs",
        "contracts",
        "figures"
    ]
    
    for dir_path in directories:
        full_path = base_dir / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        # Create __init__.py for Python packages
        if dir_path.startswith("src") or dir_path.startswith("tests"):
            init_file = full_path / "__init__.py"
            if not init_file.exists():
                init_file.touch()
    
    print(f"Project structure created at: {base_dir}")
    return True

if __name__ == "__main__":
    create_directories()