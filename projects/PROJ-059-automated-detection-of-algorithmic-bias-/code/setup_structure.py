import os
import sys
from pathlib import Path

def create_directories(project_root: Path) -> None:
    """
    Create the project directory structure for the Automated Detection of 
    Algorithmic Bias pipeline.
    
    Required directories:
    - src/bias_pipeline
    - src/cli
    - data/raw
    - data/processed
    - data/validation
    - tests/unit
    - tests/integration
    - state
    """
    directories = [
        project_root / "src" / "bias_pipeline",
        project_root / "src" / "cli",
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "data" / "validation",
        project_root / "tests" / "unit",
        project_root / "tests" / "integration",
        project_root / "state",
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        # Create __init__.py files for Python packages
        if "src" in str(directory) or "tests" in str(directory):
            init_file = directory / "__init__.py"
            if not init_file.exists():
                init_file.touch()
    
    print(f"Created {len(directories)} directories under {project_root}")

if __name__ == "__main__":
    # Determine project root (assumes script is in code/ directory)
    if len(sys.argv) > 1:
        root = Path(sys.argv[1])
    else:
        # Default to parent of script directory
        root = Path(__file__).parent.parent
    
    create_directories(root)