import os
from pathlib import Path

def ensure_dir(path: Path) -> None:
    """Ensure a directory exists, creating it if necessary."""
    path.mkdir(parents=True, exist_ok=True)

def main() -> None:
    """Create the standard project directory structure."""
    # Determine project root (parent of the 'scripts' directory)
    current_file = Path(__file__).resolve()
    scripts_dir = current_file.parent
    root = scripts_dir.parent

    # Define the directory structure to create
    directories = [
        "code/src",
        "code/src/utils",
        "code/src/config",
        "code/src/cli",
        "code/src/data",
        "code/src/data/collectors",
        "code/src/data/processing",
        "code/src/data/generators",
        "code/src/analysis",
        "code/src/services",
        "code/src/models",
        "code/tests",
        "code/tests/unit",
        "code/tests/integration",
        "code/tests/contract",
        "code/contracts",
        "code/data",
        "code/data/raw",
        "code/data/processed",
        "code/data/logs",
        "code/specs",
        "code/specs/001-climate-smart-eval",
        "code/reports",
        "code/figures",
    ]

    print(f"Creating project structure at: {root}")
    
    for dir_path in directories:
        full_path = root / dir_path
        ensure_dir(full_path)
        print(f"  Created: {dir_path}")

    print("Project structure creation complete.")

if __name__ == "__main__":
    main()