"""
Configuration validation script.
Checks that config.yaml exists, is within size limits, and contains required keys.
"""
import os
import sys
import yaml
import argparse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="Configuration Check")
    parser.add_argument('--check', action='store_true', help='Run configuration check')
    args = parser.parse_args()

    if not args.check:
        parser.print_help()
        return 1

    # Define paths relative to project root
    # Assuming this script is in code/src/config.py, project root is parent of code/
    project_root = Path(__file__).resolve().parent.parent
    config_path = project_root / "code" / "config.yaml"

    print("============================================================")
    print("Configuration Check")
    print("============================================================")

    # 1. Check if file exists
    if not config_path.exists():
        print(f"ERROR: Configuration file not found: {config_path}")
        return 1
    print(f"✓ Configuration file exists: {config_path}")

    # 2. Check size
    try:
        size = os.path.getsize(config_path)
        limit = 2048
        print(f"  Current size: {size} bytes (limit: {limit} bytes)")
        if size > limit:
            print(f"❌ FAIL: Configuration file size ({size}) exceeds limit ({limit}).")
            return 1
        print("✓ Configuration file size is within limits")
    except Exception as e:
        print(f"ERROR: Could not check file size: {e}")
        return 1

    # 3. Load and validate structure
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
    except Exception as e:
        print(f"ERROR: Could not parse YAML: {e}")
        return 1

    # Required top-level keys (based on current config structure)
    required_keys = ['hyperparameters', 'seeds', 'paths']
    missing_keys = [k for k in required_keys if k not in config]

    if missing_keys:
        print(f"ERROR: Missing required key(s): {missing_keys}")
        print("❌ FAIL: Configuration structure validation failed.")
        return 1
    
    print("✓ Configuration structure is valid")
    print("============================================================")
    print("✅ PASS: Configuration check completed successfully.")
    print("============================================================")
    return 0

if __name__ == "__main__":
    sys.exit(main())