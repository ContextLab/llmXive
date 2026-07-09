"""Script to verify data directory structure."""
import os
import sys
from pathlib import Path

def main():
    base = Path("projects/PROJ-582-socratic-transformers-dialogue-based-sel/code")
    data_dirs = ["data/raw", "data/processed", "data/results"]
    
    for d in data_dirs:
        p = base / d
        if not p.exists():
            print(f"Error: Missing directory {p}")
            sys.exit(1)
        if not (p / ".gitkeep").exists():
            print(f"Warning: Missing .gitkeep in {p}")
    
    print("Data directory structure verified.")

if __name__ == "__main__":
    main()