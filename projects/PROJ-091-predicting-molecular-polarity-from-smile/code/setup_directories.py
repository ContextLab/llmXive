import os
from pathlib import Path

def main() -> None:
    """Create project directories."""
    dirs = ["code", "tests", "data", "data/raw", "data/processed", "data/processed/analysis", "logs"]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)
        print(f"Created: {d}")

if __name__ == "__main__":
    main()
