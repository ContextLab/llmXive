import os
from pathlib import Path

def create_directories():
    """
    Initialize the project directory structure for EvoMem-Conflict Filtering.
    Creates src/, tests/, specs/, data/, docs/ and their required subdirectories.
    """
    base_path = Path(__file__).parent
    
    # Define all directories to create
    directories = [
        # Main directories
        "src",
        "tests",
        "specs",
        "data",
        "docs",
        
        # src subdirectories
        "src/agents",
        "src/heuristics",
        "src/data/generators",
        "src/data/benchmarks",
        "src/analysis",
        "src/utils",
        "src/cli",
        
        # tests subdirectories
        "tests/unit",
        "tests/integration",
        "tests/contract",
        
        # specs subdirectories
        "specs/001-evoconflict-filtering",
        "specs/001-evoconflict-filtering/contracts",
        
        # data subdirectories (needed for outputs)
        "data/raw",
        "data/processed",
        "data/logs",
        "figures"
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
                raise RuntimeError(f"Path exists but is not a directory: {full_path}")
    
    print(f"Created {created_count} directories.")
    return True

if __name__ == "__main__":
    create_directories()
