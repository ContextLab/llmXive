import os
import sys
from pathlib import Path

def create_directories():
    """Create the standard project directory structure."""
    dirs = [
        "src",
        "data/raw",
        "data/derived",
        "data/annotations",
        "results",
        "tests",
        "specs",
        "logs",
        "code"
    ]
    
    for d in dirs:
        path = Path(d)
        path.mkdir(parents=True, exist_ok=True)
        print(f"Created/Verified: {path}")

if __name__ == "__main__":
    create_directories()
    print("Project structure setup complete.")