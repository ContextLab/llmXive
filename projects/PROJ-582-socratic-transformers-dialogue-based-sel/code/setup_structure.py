import os
from pathlib import Path

def create_directories():
    """Create the full project directory structure for PROJ-582."""
    base = Path("projects/PROJ-582-socratic-transformers-dialogue-based-sel/code")
    
    dirs = [
        base,
        base / "src",
        base / "src" / "data",
        base / "src" / "train",
        base / "src" / "eval",
        base / "src" / "analyze",
        base / "src" / "utils",
        base / "tests",
        base / "tests" / "contract",
        base / "tests" / "integration",
    ]
    
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {d}")

def main():
    create_directories()
    print("Project directory structure creation complete.")

if __name__ == "__main__":
    main()
