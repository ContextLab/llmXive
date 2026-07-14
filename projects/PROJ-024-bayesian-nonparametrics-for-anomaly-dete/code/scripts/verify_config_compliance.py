"""
Script to verify config.yaml compliance.
Checks that the file exists and its size is under 2048 bytes.
"""
import os
import sys
from pathlib import Path

# Project root is parent of 'code' directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_PATH = PROJECT_ROOT / "code" / "config.yaml"
LIMIT = 2048

def main():
    print("Configuration Compliance Check")
    print("=" * 40)
    
    if not CONFIG_PATH.exists():
        print(f"ERROR: Configuration file not found at {CONFIG_PATH}")
        return 1
    
    file_size = os.path.getsize(CONFIG_PATH)
    print(f"Configuration file: {CONFIG_PATH}")
    print(f"Current size: {file_size} bytes")
    print(f"Limit: {LIMIT} bytes")
    
    if file_size > LIMIT:
        print(f"❌ FAIL: Configuration size ({file_size}) exceeds limit ({LIMIT}).")
        print("Please run migrate_config.py to move derived statistics to the state file.")
        return 1
    
    print("✅ PASS: Configuration size is within limits.")
    return 0

if __name__ == "__main__":
    sys.exit(main())