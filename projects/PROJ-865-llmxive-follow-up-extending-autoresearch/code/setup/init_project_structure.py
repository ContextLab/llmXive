import os
import sys
from pathlib import Path

def ensure_directory(path: Path) -> None:
    """Create directory if it does not exist."""
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
    # Ensure a .gitkeep file exists to make the directory committed
    gitkeep = path / ".gitkeep"
    if not gitkeep.exists():
        gitkeep.touch()

def main() -> int:
    """Initialize the full project directory structure and create .gitkeep files."""
    base = Path(".")
    
    # Define all required directories based on T001 spec
    dirs = [
        "code",
        "data",
        "data/raw",
        "data/derived",
        "data/artifacts",
        "specs/001-llmxive-followup/contracts",
        "code/01_data_ingestion",
        "code/02_annotation_distillation",
        "code/03_execution",
        "code/04_analysis",
        "code/utils",
        "code/tests",
    ]
    
    for d in dirs:
        ensure_directory(base / d)
    
    print("Project structure initialized successfully.")
    print("Created directories and .gitkeep files in:")
    for d in dirs:
        print(f"  - {d}/")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
