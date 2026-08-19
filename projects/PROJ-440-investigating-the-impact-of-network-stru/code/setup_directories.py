import os
from pathlib import Path

def setup_directories():
    """
    Creates the required directory structure for the project:
    code/, data/, data/raw/, data/processed/, data/analysis/,
    tests/, contracts/, state/
    """
    base_path = Path(".")
    directories = [
        "code",
        "data",
        "data/raw",
        "data/processed",
        "data/analysis",
        "tests",
        "contracts",
        "state"
    ]

    created_count = 0
    for dir_name in directories:
        full_path = base_path / dir_name
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
        # Ensure existence even if it was already there
        if full_path.exists():
            pass # Already exists or just created

    return created_count

if __name__ == "__main__":
    count = setup_directories()
    print(f"Directory setup complete. Created/verified {count} new directories.")
