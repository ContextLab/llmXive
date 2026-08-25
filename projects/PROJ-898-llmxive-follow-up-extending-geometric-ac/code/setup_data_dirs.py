import os
import sys
from typing import List, Optional

def ensure_gitkeep(directory: str) -> None:
    """
    Ensure the given directory exists and contains a .gitkeep file.
    
    Args:
        directory: Path to the directory to ensure exists.
    """
    os.makedirs(directory, exist_ok=True)
    gitkeep_path = os.path.join(directory, ".gitkeep")
    if not os.path.exists(gitkeep_path):
        with open(gitkeep_path, "w") as f:
            f.write("# Keep this directory in git\n")
        print(f"Created .gitkeep in {directory}")
    else:
        print(f".gitkeep already exists in {directory}")


def main() -> None:
    """
    Main entry point to set up the data directory structure.
    
    Creates the following directories if they do not exist:
    - data/raw
    - data/generated
    - data/results
    
    And ensures each contains a .gitkeep file.
    """
    base_path = "data"
    sub_dirs = ["raw", "generated", "results"]
    
    for sub_dir in sub_dirs:
        full_path = os.path.join(base_path, sub_dir)
        ensure_gitkeep(full_path)
    
    print("Data directory structure setup complete.")


if __name__ == "__main__":
    main()
