import os
from pathlib import Path

def create_directories(root_path: str = ".") -> None:
    """
    Create the project directory structure as per the implementation plan.
    
    Directories created:
    - src/ (source code)
    - tests/ (unit and integration tests)
    - data/ (raw and processed data)
    - output/ (final reports and figures)
    
    Args:
        root_path: The root directory where the structure will be created.
    """
    root = Path(root_path)
    
    directories = [
        root / "src",
        root / "tests",
        root / "data",
        root / "data" / "raw",
        root / "data" / "processed",
        root / "output",
        root / "output" / "temporal_profiles",
        root / "contracts",
        root / "logs",
        root / "specs",
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {directory}")

if __name__ == "__main__":
    create_directories()