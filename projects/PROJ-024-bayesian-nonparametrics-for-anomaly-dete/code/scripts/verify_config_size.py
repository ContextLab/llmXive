"""
Verification script for T060/T061.
Checks that code/config.yaml is under 2048 bytes.
"""
import os
import sys
from pathlib import Path

def main():
    config_path = Path(__file__).resolve().parent.parent / "code" / "config.yaml"
    
    if not config_path.exists():
        print(f"ERROR: Config file not found at {config_path}")
        sys.exit(1)

    size = os.path.getsize(config_path)
    limit = 2048

    print(f"Checking config size: {config_path}")
    print(f"Current size: {size} bytes")
    print(f"Limit: {limit} bytes")

    if size > limit:
        print(f"FAIL: Config size ({size}) exceeds limit ({limit})")
        sys.exit(1)
    else:
        print(f"PASS: Config size is within limits.")
        sys.exit(0)

if __name__ == "__main__":
    main()