import subprocess
import sys
import os

def main():
    """Run black formatting on the project."""
    print("Running black format...")
    try:
        subprocess.run(
            ["black", "code/", "tests/"],
            check=True,
            text=True,
        )
        print("Formatting passed.")
        sys.exit(0)
    except subprocess.CalledProcessError:
        print("Formatting failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
