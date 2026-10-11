"""
Simple checksum utility used in the quick‑start verification step.

The script walks the supplied directory (recursively) and prints a
SHA‑256 checksum for each file it encounters.  It returns a non‑zero
exit status if the argument is missing or the path is not a directory.
"""

import sys
from pathlib import Path

from utils import calculate_file_checksum

def main():
    if len(sys.argv) != 2:
        print("Usage: python checksum.py <directory>", file=sys.stderr)
        sys.exit(1)

    target_dir = Path(sys.argv[1])
    if not target_dir.is_dir():
        print(f"Error: {target_dir} is not a directory", file=sys.stderr)
        sys.exit(1)

    for file_path in target_dir.rglob("*"):
        if file_path.is_file():
            checksum = calculate_file_checksum(file_path)
            print(f"{file_path}: {checksum}")

if __name__ == "__main__":
    main()