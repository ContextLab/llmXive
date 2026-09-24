import os
from pathlib import Path
from config import ensure_directories

def main():
    """Setup project directories."""
    ensure_directories()
    print("Project directories created.")

if __name__ == "__main__":
    main()
