import os
import sys
from pathlib import Path

def create_code_directory():
    """Create code directory and init."""
    Path('code').mkdir(parents=True, exist_ok=True)
    (Path('code') / '__init__.py').touch(exist_ok=True)
    print("Code directory created.")

def main():
    create_code_directory()

if __name__ == "__main__":
    main()
