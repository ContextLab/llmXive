import os
import sys
from pathlib import Path

def create_tests_directory():
    """Create tests directory and init."""
    Path('tests').mkdir(parents=True, exist_ok=True)
    (Path('tests') / '__init__.py').touch(exist_ok=True)
    print("Tests directory created.")

def main():
    create_tests_directory()

if __name__ == "__main__":
    main()
