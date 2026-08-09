import os
import sys
from pathlib import Path

def create_state_directory():
    """Create state directory and init."""
    Path('state').mkdir(parents=True, exist_ok=True)
    (Path('state') / '__init__.py').touch(exist_ok=True)
    print("State directory created.")

def main():
    create_state_directory()

if __name__ == "__main__":
    main()
