"""Project setup module."""
import os
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from config import ensure_directories

def main():
    ensure_directories()
    print("Project directories created.")

if __name__ == "__main__":
    main()
