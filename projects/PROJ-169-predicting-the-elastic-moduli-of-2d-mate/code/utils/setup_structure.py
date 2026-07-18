import os
from pathlib import Path

def main():
    """Create the required directory structure for the project."""
    root = Path(__file__).resolve().parent.parent.parent
    
    dirs = [
        root / "code",
        root / "data" / "raw",
        root / "data" / "processed",
        root / "data" / "results",
        root / "tests" / "unit",
        root / "tests" / "integration",
        root / "docs",
        root / "state" / "projects",
    ]
    
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {d}")
    
    print("Project structure initialized successfully.")

if __name__ == "__main__":
    main()