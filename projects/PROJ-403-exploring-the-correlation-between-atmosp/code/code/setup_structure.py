import os
from pathlib import Path

def main():
    """
    Initialize the project directory structure.
    Creates required directories and __init__.py files.
    """
    root = Path(__file__).resolve().parent.parent
    
    # Define required directories
    dirs = [
        "src",
        "src/utils",
        "src/data",
        "src/cli",
        "src/viz",
        "tests",
        "tests/unit",
        "tests/integration",
        "data",
        "data/raw",
        "data/processed",
        "figures",
        "logs",
        "report",
        "artifacts"
    ]

    # Create directories
    for dir_path in dirs:
        full_path = root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created: {full_path.relative_to(root)}")

    # Create __init__.py files in src and tests subdirectories
    init_dirs = ["src", "tests", "src/utils", "src/data", "src/cli", "src/viz", "tests/unit", "tests/integration"]
    for dir_path in init_dirs:
        full_path = root / dir_path / "__init__.py"
        if not full_path.exists():
            full_path.touch()
            print(f"Created: {full_path.relative_to(root)}")

    print("Project structure initialization complete.")

if __name__ == "__main__":
    main()
