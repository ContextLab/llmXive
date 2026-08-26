import os
from pathlib import Path

def create_directory_structure(root_dir: str = ".") -> None:
    """
    Create the required directory structure for the project.
    
    This function creates the following directories relative to root_dir:
    - data/raw, data/processed
    - results, state, contracts, logs, docs
    - src, src/data, src/graphs, src/metrics, src/analysis, src/utils
    - tests/unit, tests/integration, tests/contract
    
    Args:
        root_dir: The root directory relative to which paths are created.
                 Defaults to current directory.
    """
    base_path = Path(root_dir)
    
    # Define all required directories
    directories = [
        "data/raw",
        "data/processed",
        "results",
        "state",
        "contracts",
        "logs",
        "docs",
        "src",
        "src/data",
        "src/graphs",
        "src/metrics",
        "src/analysis",
        "src/utils",
        "tests/unit",
        "tests/integration",
        "tests/contract",
    ]
    
    created_count = 0
    for dir_path in directories:
        full_path = base_path / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
        else:
            # Ensure it's actually a directory
            if not full_path.is_dir():
                raise FileExistsError(
                    f"Path exists but is not a directory: {full_path}"
                )
    
    print(f"Directory structure ready. Created {created_count} new directories.")

if __name__ == "__main__":
    import sys
    
    # Allow optional argument for root directory
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    create_directory_structure(root)