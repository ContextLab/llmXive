"""
Configuration check script for the project.
Validates that config.yaml exists, is within size limits, and contains required keys.
"""
import os
import sys
import yaml
import argparse
from pathlib import Path

# Project root is the parent of the 'code' directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "code" / "config.yaml"
SIZE_LIMIT = 2048  # bytes

# Updated required keys to match the actual config.yaml structure (T007)
# T007 specifies: "ONLY hyperparameters, seeds, and base paths"
# We check for 'hyperparameters', 'seeds', and 'base_paths' as per the spec.
REQUIRED_KEYS = ['hyperparameters', 'seeds', 'base_paths']

def main():
    parser = argparse.ArgumentParser(description="Check project configuration validity.")
    parser.add_argument('--check', action='store_true', help="Run configuration validation checks.")
    args = parser.parse_args()

    if args.check:
        print("============================================================")
        print("Configuration Check")
        print("============================================================")
        
        # 1. Check if file exists
        if not CONFIG_PATH.exists():
            print(f"ERROR: Configuration file not found: {CONFIG_PATH}")
            return 1
        
        print(f"✓ Configuration file exists: {CONFIG_PATH}")

        # 2. Check file size
        file_size = os.path.getsize(CONFIG_PATH)
        print(f"  Current size: {file_size} bytes (limit: {SIZE_LIMIT} bytes)")
        
        if file_size > SIZE_LIMIT:
            print(f"ERROR: Configuration file size exceeds limit ({SIZE_LIMIT} bytes).")
            print("Note: Derived statistics must be migrated to the state file per FR-009.")
            return 1
        
        print("✓ Configuration file size is within limits")

        # 3. Load and validate structure
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            print(f"ERROR: Failed to parse YAML: {e}")
            return 1

        missing_keys = [key for key in REQUIRED_KEYS if key not in config]
        if missing_keys:
            print(f"ERROR: Missing required key(s): {', '.join(missing_keys)}")
            print("❌ FAIL: Configuration structure validation failed")
            return 1

        print("✓ Configuration structure is valid")
        print("============================================================")
        print("✅ PASS: All checks successful")
        return 0

    return 0

if __name__ == "__main__":
    sys.exit(main())