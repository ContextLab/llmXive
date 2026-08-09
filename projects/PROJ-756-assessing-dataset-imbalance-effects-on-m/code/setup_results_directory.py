import os
import sys
from pathlib import Path

def create_results_directory():
    """Create results directory and init."""
    Path('results').mkdir(parents=True, exist_ok=True)
    (Path('results') / '__init__.py').touch(exist_ok=True)
    print("Results directory created.")

def main():
    create_results_directory()

if __name__ == "__main__":
    main()
