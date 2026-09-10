import os
from pathlib import Path

def main():
    """
    Create required project directories: data/raw/, data/derived/, code/, tests/.
    This script ensures the directory structure exists for the llmXive pipeline.
    """
    # Define relative paths based on project root
    directories = [
        "data/raw",
        "data/derived",
        "code",
        "tests"
    ]

    for dir_path in directories:
        path = Path(dir_path)
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {path}")
        else:
            print(f"Directory already exists: {path}")

    # Verify creation by listing contents
    print("\nVerification of created directories:")
    for dir_path in directories:
        path = Path(dir_path)
        if path.exists():
            print(f"  [OK] {path}")
        else:
            print(f"  [FAIL] {path} was not created")

if __name__ == "__main__":
    main()
