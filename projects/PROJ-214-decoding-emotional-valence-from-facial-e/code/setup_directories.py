import os
from pathlib import Path

def main():
    """
    Create the required directory structure for the project.
    Creates: data/raw, data/processed, data/models
    """
    base_dir = Path(__file__).parent.parent
    data_dirs = [
        base_dir / "data" / "raw",
        base_dir / "data" / "processed",
        base_dir / "data" / "models",
    ]

    for dir_path in data_dirs:
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Ensured directory exists: {dir_path}")

    # Verify existence
    for dir_path in data_dirs:
        if not dir_path.exists():
            raise RuntimeError(f"Failed to create directory: {dir_path}")
        if not dir_path.is_dir():
            raise RuntimeError(f"Path exists but is not a directory: {dir_path}")

    print("Directory structure setup complete.")

if __name__ == "__main__":
    main()