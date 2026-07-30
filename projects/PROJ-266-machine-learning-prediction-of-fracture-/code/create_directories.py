import os
import sys

def main():
    """Create the required code directory structure."""
    dirs = [
        "code",
        "code/data",
        "code/models",
        "code/train",
        "code/explain",
    ]

    created = 0
    for d in dirs:
        if not os.path.exists(d):
            os.makedirs(d, exist_ok=True)
            created += 1
            print(f"Created directory: {d}")
        else:
            print(f"Directory exists: {d}")

    print(f"Total directories created in this run: {created}")
    return 0

if __name__ == "__main__":
    sys.exit(main())