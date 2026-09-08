"""
Script to create required data directories.
"""
import os
from pathlib import Path

def main():
    base = Path(__file__).parent.parent
    data_dir = base / "data"
    dirs = ["raw", "interim", "processed", "final"]
    
    for d in dirs:
        path = data_dir / d
        path.mkdir(parents=True, exist_ok=True)
        print(f"Created: {path}")

if __name__ == "__main__":
    main()
