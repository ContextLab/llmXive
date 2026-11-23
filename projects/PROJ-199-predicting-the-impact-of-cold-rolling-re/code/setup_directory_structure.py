import os
from pathlib import Path


def main() -> None:
    """
    Main entry point to set up the standard project directory structure.
    Creates code/, data/, tests/, and docs/ directories.
    """
    root_dirs = ["code", "data", "tests", "docs"]
    
    for dir_name in root_dirs:
        path = Path(dir_name)
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {path}")
        else:
            print(f"Directory exists: {path}")


if __name__ == "__main__":
    main()