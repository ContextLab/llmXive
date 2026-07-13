"""
Verify config.yaml size compliance (<2KB).
This script checks the size of code/config.yaml and exits with an error if it exceeds 2048 bytes.
"""
import os
import sys
from pathlib import Path

def main():
    # Determine project root
    current = Path(__file__).resolve()
    # Script is at code/scripts/verify_config_compliance.py
    # Project root is 2 levels up: scripts -> code -> project_root
    project_root = current.parent.parent
    
    config_path = project_root / "code" / "config.yaml"
    
    if not config_path.exists():
        print(f"ERROR: Config file not found at {config_path}")
        return 1
    
    config_size = os.path.getsize(config_path)
    max_size = 2048  # 2KB
    
    print(f"Config file: {config_path}")
    print(f"Size: {config_size} bytes")
    print(f"Max allowed: {max_size} bytes")
    
    if config_size > max_size:
        print(f"ERROR: Config file exceeds 2KB limit by {config_size - max_size} bytes")
        return 1
    else:
        print("SUCCESS: Config file is under 2KB limit")
        return 0

if __name__ == "__main__":
    sys.exit(main())