"""
Script to verify config.yaml compliance (size < 2KB).
This script is invoked by the run-book to enforce the constraint.
"""
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "code" / "config.yaml"
LIMIT = 2048

def main():
    if not CONFIG_PATH.exists():
        print(f"ERROR: Config file not found: {CONFIG_PATH}")
        sys.exit(1)

    size = os.path.getsize(CONFIG_PATH)
    print(f"Config file: {CONFIG_PATH}")
    print(f"Size: {size} bytes")
    print(f"Limit: {LIMIT} bytes")

    if size > LIMIT:
        print(f"FAIL: Config file size ({size}) exceeds limit ({LIMIT}).")
        sys.exit(1)
    else:
        print("PASS: Config file size is within limits.")
        sys.exit(0)

if __name__ == "__main__":
    main()