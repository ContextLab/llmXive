import os
from pathlib import Path

def create_directory_structure():
    """
    Creates the project directory structure for the llmXive pipeline.
    Ensures src/, tests/, data/ (with subdirs), and code/ exist.
    """
    # Define root relative to this script (assuming script is in code/)
    # The task requires paths relative to project root: code/, data/, tests/, src/
    # Since this script is in code/, we go up one level to project root.
    root = Path(__file__).parent.parent

    dirs_to_create = [
        "src",
        "src/utils",
        "src/data",
        "src/compression",
        "src/pe",
        "tests",
        "tests/unit",
        "tests/integration",
        "tests/contract",
        "data/raw",
        "data/interim",
        "data/processed",
        "data/external",
        "code",
        "code/provenance",
        "reports",
        "figures",
        "specs",
    ]

    created = []
    for d in dirs_to_create:
        full_path = root / d
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created.append(str(full_path.relative_to(root)))
        else:
            # Ensure it's a directory
            if full_path.is_file():
                raise RuntimeError(f"Path exists but is a file: {full_path}")

    # Create __init__.py files to ensure they are Python packages
    for d in dirs_to_create:
        full_path = root / d
        if full_path.is_dir():
            init_file = full_path / "__init__.py"
            if not init_file.exists():
                init_file.touch()
                created.append(f"{d}/__init__.py")

    return created

if __name__ == "__main__":
    print("Creating project directory structure...")
    new_dirs = create_directory_structure()
    print(f"Created directories: {new_dirs}")
