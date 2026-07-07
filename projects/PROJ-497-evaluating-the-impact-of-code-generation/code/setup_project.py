import os
import sys
from pathlib import Path

def main():
    """
    Create the standard project directory structure for llmXive.
    Creates: code/, data/, results/, state/, tests/
    """
    root = Path(".")
    directories = [
        "code",
        "data",
        "results",
        "state",
        "tests",
        "data/raw",
        "data/processed",
        "data/generated",
        "results/figures",
        "tests/unit",
        "tests/integration",
        "tests/contract",
    ]

    created_count = 0
    for dir_name in directories:
        target = root / dir_name
        if not target.exists():
            target.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {target}")
            created_count += 1
        else:
            print(f"Directory exists: {target}")

    print(f"\nProject structure initialization complete. {created_count} new directories created.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
