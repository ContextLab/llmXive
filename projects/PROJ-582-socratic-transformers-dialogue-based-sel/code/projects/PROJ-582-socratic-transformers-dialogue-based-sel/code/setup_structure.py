"""Script to create the project directory structure and placeholder files."""
import os
import sys
from pathlib import Path

def main():
    base = Path("projects/PROJ-582-socratic-transformers-dialogue-based-sel/code")
    dirs = [
        "src/data", "src/train", "src/eval", "src/analyze", "src/utils",
        "tests/contract", "tests/integration",
        "data/raw", "data/processed", "data/results"
    ]
    
    for d in dirs:
        p = base / d
        p.mkdir(parents=True, exist_ok=True)
        # Create .gitkeep in data subdirs to ensure they are tracked
        if d.startswith("data/"):
            (p / ".gitkeep").touch()
    
    # Ensure __init__.py files exist if not handled by other tasks
    init_dirs = [
        "src", "src/data", "src/train", "src/eval", "src/analyze", "src/utils",
        "tests", "tests/contract", "tests/integration"
    ]
    for d in init_dirs:
        p = base / d / "__init__.py"
        if not p.exists():
            p.write_text('"""Auto-generated init."""\n')
    
    print(f"Project structure created at {base}")

if __name__ == "__main__":
    main()
