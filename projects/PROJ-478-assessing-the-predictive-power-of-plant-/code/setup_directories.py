import os
import sys
from pathlib import Path

def create_directories():
    """
    Creates the core source directories required for the project.
    Ensures src/, src/data/, src/modeling/, src/analysis/, and src/utils/ exist.
    """
    root = Path(__file__).parent
    dirs = [
        root / "src",
        root / "src" / "data",
        root / "src" / "modeling",
        root / "src" / "analysis",
        root / "src" / "utils",
    ]

    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        # Create __init__.py to ensure they are treated as packages
        init_file = d / "__init__.py"
        if not init_file.exists():
            init_file.touch()
    
    return [str(d) for d in dirs]

if __name__ == "__main__":
    created = create_directories()
    print(f"Created directories: {created}")
