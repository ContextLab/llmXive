import os
from pathlib import Path

def main():
    dirs = ["data", "data/raw", "data/processed", "data/final", "code", "tests", "docs", "figures"]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)

if __name__ == "__main__":
    main()
