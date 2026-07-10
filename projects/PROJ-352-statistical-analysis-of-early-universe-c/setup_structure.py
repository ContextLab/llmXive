"""
Project initialization script to create the required directory structure.
"""
import os
import sys

def main():
    """Create the project directory structure."""
    base_dirs = [
        "code",
        "data/raw",
        "data/processed",
        "output",
        "tests"
    ]

    created = []
    for d in base_dirs:
        if not os.path.exists(d):
            os.makedirs(d)
            created.append(d)
            print(f"Created directory: {d}")
        else:
            print(f"Directory exists: {d}")

    if not created:
        print("All directories already exist.")
    else:
        print(f"Created {len(created)} directories.")

    return 0

if __name__ == "__main__":
    sys.exit(main())