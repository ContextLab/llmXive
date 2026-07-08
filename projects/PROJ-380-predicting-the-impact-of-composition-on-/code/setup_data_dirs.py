import os
from pathlib import Path

def main():
    """Create the required directory structure."""
    base = Path(__file__).parent.parent
    dirs = [
        base / "code",
        base / "code" / "data",
        base / "code" / "models",
        base / "code" / "viz",
        base / "code" / "utils",
        base / "data",
        base / "data" / "raw",
        base / "data" / "processed",
        base / "data" / "artifacts",
        base / "tests",
        base / "tests" / "unit",
        base / "tests" / "integration",
        base / "docs",
        base / "state",
        base / "state" / "projects"
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    print("Directories created successfully.")

if __name__ == "__main__":
    main()
