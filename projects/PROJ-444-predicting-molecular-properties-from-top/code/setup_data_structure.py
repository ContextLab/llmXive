import os
import json
from pathlib import Path
from typing import List

def ensure_directory(dir_path: Path) -> None:
    """Ensure a directory exists, creating it if necessary."""
    dir_path.mkdir(parents=True, exist_ok=True)

def initialize_file(file_path: Path, content: str = "") -> None:
    """Initialize a file with optional content, creating parent directories if needed."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content)

def main() -> None:
    """Create the project structure for PROJ-444-predicting-molecular-properties-from-top."""
    base_path = Path("projects/PROJ-444-predicting-molecular-properties-from-top")
    
    # Create base directories
    ensure_directory(base_path)
    ensure_directory(base_path / "code")
    ensure_directory(base_path / "code/utils")
    ensure_directory(base_path / "data")
    ensure_directory(base_path / "data/raw")
    ensure_directory(base_path / "data/processed")
    ensure_directory(base_path / "data/logs")
    ensure_directory(base_path / "tests")
    ensure_directory(base_path / "tests/unit")
    ensure_directory(base_path / "tests/integration")
    ensure_directory(base_path / "tests/contract")
    ensure_directory(base_path / "reports")
    ensure_directory(base_path / "reports/metrics")
    ensure_directory(base_path / "reports/figures")
    ensure_directory(base_path / "specs")
    ensure_directory(base_path / "state")
    
    # Initialize state tracking file
    initialize_file(
        base_path / "state" / "pipeline_state.json",
        json.dumps({"last_run": None, "status": "initialized"}, indent=2)
    )
    
    # Initialize empty log file
    initialize_file(base_path / "data" / "logs" / "invalid_smiles.log")
    
    # Initialize .gitkeep files to ensure directories are tracked in git
    gitkeep_content = "# Keep this directory in git\n"
    for dir_path in base_path.rglob("*"):
        if dir_path.is_dir():
            initialize_file(dir_path / ".gitkeep", gitkeep_content)

if __name__ == "__main__":
    main()
