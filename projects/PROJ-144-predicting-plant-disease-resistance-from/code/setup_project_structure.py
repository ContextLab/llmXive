import os
import sys
from pathlib import Path

def create_structure():
    dirs = [
        "code",
        "code/data",
        "code/modeling",
        "code/utils",
        "data/raw",
        "data/processed",
        "tests",
        "tests/unit",
        "tests/integration",
        "state",
        "results",
        "figures",
        "specs"
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)
    print("Project structure created.")

if __name__ == "__main__":
    create_structure()
