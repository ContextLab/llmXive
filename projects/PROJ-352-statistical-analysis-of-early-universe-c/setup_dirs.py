"""
Script to initialize the project directory structure.
Run this once to ensure all required folders exist.
"""
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
DIRS = [
    "code",
    "data/raw",
    "data/processed",
    "output",
    "tests"
]

def main():
    for d in DIRS:
        path = os.path.join(ROOT, d)
        if not os.path.exists(path):
            os.makedirs(path)
            print(f"Created directory: {path}")
        else:
            print(f"Directory exists: {path}")

if __name__ == "__main__":
    main()