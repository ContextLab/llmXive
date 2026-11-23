import os
import sys
from pathlib import Path

def create_structure(root_path: str) -> None:
    """
    Create the standard project directory structure.
    
    Creates the following directories relative to root_path:
    - src/ (source code)
    - src/cli/
    - src/data/
    - src/eval/
    - src/models/
    - src/utils/
    - data/ (data storage)
    - data/raw/
    - data/processed/
    - data/artifacts/
    - data/references/
    - tests/ (test suite)
    - tests/unit/
    - tests/integration/
    - tests/contract/
    - state/ (state management)
    - specs/ (feature specifications)
    - docs/ (documentation)
    
    Args:
        root_path: The root directory where the structure will be created.
    """
    root = Path(root_path)
    
    # Define directory structure
    directories = [
        "src",
        "src/cli",
        "src/data",
        "src/eval",
        "src/models",
        "src/utils",
        "data/raw",
        "data/processed",
        "data/artifacts",
        "data/references",
        "tests/unit",
        "tests/integration",
        "tests/contract",
        "state",
        "specs",
        "docs",
    ]
    
    created = []
    for dir_path in directories:
        full_path = root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        created.append(str(full_path))
        # Create __init__.py for Python packages
        if dir_path.startswith("src") or dir_path.startswith("tests"):
          init_file = full_path / "__init__.py"
          if not init_file.exists():
              init_file.touch()
    
    # Create README in data directories to ensure they are tracked
    for data_sub in ["raw", "processed", "artifacts", "references"]:
        readme_path = root / "data" / data_sub / ".gitkeep"
        if not readme_path.exists():
            readme_path.touch()
    
    print(f"Project structure created at {root}")
    for p in created:
        print(f"  - {p}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        create_structure(sys.argv[1])
    else:
        # Default to current directory if no argument provided
        create_structure(".")