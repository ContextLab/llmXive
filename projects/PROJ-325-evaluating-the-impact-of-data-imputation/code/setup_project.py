import os
from pathlib import Path

def main():
    """
    Create the project directory structure as defined in the implementation plan.
    Creates: code/, data/raw, data/processed, tests/, specs/contracts, figures/
    """
    root = Path(".")
    dirs = [
        "code",
        "data/raw",
        "data/processed",
        "data/figures",
        "tests",
        "tests/contract",
        "tests/integration",
        "tests/unit",
        "specs/contracts",
        "figures",
        "state"
    ]

    created = []
    for d in dirs:
        path = root / d
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            created.append(str(path))
            print(f"Created directory: {path}")
        else:
            print(f"Directory already exists: {path}")

    if not created:
        print("No new directories created. Structure already exists.")
    else:
        print(f"\nTotal directories created: {len(created)}")

    return 0

if __name__ == "__main__":
    exit(main())
