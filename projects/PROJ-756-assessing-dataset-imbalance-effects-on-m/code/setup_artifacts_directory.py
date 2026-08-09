import os
import sys
from pathlib import Path

def create_artifacts_directory():
    """Create artifacts directory and init."""
    Path('artifacts').mkdir(parents=True, exist_ok=True)
    (Path('artifacts') / '__init__.py').touch(exist_ok=True)
    print("Artifacts directory created.")

def main():
    create_artifacts_directory()

if __name__ == "__main__":
    main()
