import os
import sys
from pathlib import Path

def create_directory(path: str) -> None:
    """Create a directory if it does not exist."""
    Path(path).mkdir(parents=True, exist_ok=True)
    print(f"Created directory: {path}")

def main() -> None:
    """Create the project directory structure for llmXive PROJ-560."""
    base = Path(".")
    
    # Core code directories
    create_directory(str(base / "code" / "src"))
    create_directory(str(base / "code" / "tests"))
    
    # Data directories
    create_directory(str(base / "data" / "raw"))
    create_directory(str(base / "data" / "processed"))
    create_directory(str(base / "data" / "synthetic"))
    create_directory(str(base / "data" / "derivation_logs"))
    
    # State directory for the specific project
    project_state_dir = base / "state" / "projects" / "PROJ-560-embodied-curriculum-learning-physical-si"
    create_directory(str(project_state_dir))
    
    print("Project structure initialization complete.")

if __name__ == "__main__":
    main()
