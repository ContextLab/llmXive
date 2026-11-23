import os
import sys

def check_structure():
    """
    Verifies that the required project directory structure exists.
    Returns True if all directories are present, False otherwise.
    """
    required_dirs = [
        "code",
        "code/models",
        "code/utils",
        "code/validators",
        "data",
        "data/external",
        "data/processed",
        "data/generated",
        "tests",
        "tests/unit",
        "tests/integration",
        "docs",
        "figures"
    ]

    all_present = True
    for dir_path in required_dirs:
        if not os.path.isdir(dir_path):
            print(f"MISSING: {dir_path}")
            all_present = False
        else:
            print(f"OK: {dir_path}")

    return all_present

if __name__ == "__main__":
    if check_structure():
        print("\nProject structure validation PASSED.")
        sys.exit(0)
    else:
        print("\nProject structure validation FAILED.")
        sys.exit(1)
