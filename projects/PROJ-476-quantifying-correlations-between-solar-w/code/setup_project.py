import os
from pathlib import Path

def setup():
    """Create the directory hierarchy required by the specification."""
    directories = [
        "code/data",
        "code/analysis",
        "code/viz",
        "code/tests",
        "data/raw",
        "data/processed",
        "results",
        "figures",
    ]
    for d in directories:
        path = Path(d)
        path.mkdir(parents=True, exist_ok=True)
        print(f"Ensured directory exists: {d}")

if __name__ == "__main__":
    setup()
