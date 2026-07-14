"""
Script to verify config.yaml compliance with project constraints.
Specifically checks that config.yaml size is < 2KB.
"""
import os
import sys
from pathlib import Path

# Project root is the parent of the 'code' directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "code" / "config.yaml"
SIZE_LIMIT = 2048  # bytes

def main():
    print("Verifying config compliance...")
    
    if not CONFIG_PATH.exists():
        print(f"ERROR: Configuration file not found: {CONFIG_PATH}")
        return 1

    file_size = os.path.getsize(CONFIG_PATH)
    print(f"Config file: {CONFIG_PATH}")
    print(f"Size: {file_size} bytes")
    print(f"Limit: {SIZE_LIMIT} bytes")

    if file_size > SIZE_LIMIT:
        print(f"❌ FAIL: Config file size ({file_size}) exceeds limit ({SIZE_LIMIT}).")
        return 1
    
    print("✅ PASS: Config file size is within limits.")
    return 0

if __name__ == "__main__":
    sys.exit(main())