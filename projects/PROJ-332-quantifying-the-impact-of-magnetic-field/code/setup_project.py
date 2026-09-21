import os
from pathlib import Path

def create_directories():
    """Create the project directory structure as specified in plan.md."""
    root = Path(__file__).parent.parent
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "outputs",
        "tests",
        "contracts",
        ".github/workflows",
    ]

    created = []
    for dir_path in directories:
        full_path = root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        created.append(str(full_path))

    return created

def main():
    print("Creating project directory structure...")
    dirs = create_directories()
    print(f"Created directories: {', '.join(dirs)}")

if __name__ == "__main__":
    main()
