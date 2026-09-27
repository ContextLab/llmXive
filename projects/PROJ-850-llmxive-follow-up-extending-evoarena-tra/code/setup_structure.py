import os
from pathlib import Path
import sys

# Ensure the project root is in the path
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.seencing import set_deterministic_seed

def create_directories():
    """
    Initialize project directory structure.
    Sets deterministic seed before creating directories to ensure
    consistent behavior if any random operations are involved.
    """
    # Set deterministic seed
    set_deterministic_seed()

    # Define directories
    base_dirs = [
        "src",
        "tests",
        "specs",
        "data",
        "docs",
        "data/raw",
        "data/processed",
        "data/logs",
        "figures",
        "src/agents",
        "src/heuristics",
        "src/data/generators",
        "src/data/benchmarks",
        "src/analysis",
        "src/utils",
        "src/cli",
        "tests/unit",
        "tests/integration",
        "tests/contract",
        "specs/001-evoconflict-filtering/contracts",
    ]

    for dir_path in base_dirs:
        path = Path(dir_path)
        path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {path}")

    print("Project directory structure initialized successfully.")

if __name__ == "__main__":
    create_directories()
