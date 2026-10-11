import os
from pathlib import Path

def main():
    """
    Creates the project directory structure and adds .gitkeep files
    to ensure directories are tracked by version control.
    """
    dirs = [
        "code",
        "data/raw",
        "data/processed",
        "models",
        "metrics",
        "logs",
        "reports",
        "tests",
        "contracts"
    ]
    
    for d in dirs:
        path = Path(d)
        path.mkdir(parents=True, exist_ok=True)
        (path / ".gitkeep").touch()
        print(f"Created directory: {d}")

if __name__ == "__main__":
    main()