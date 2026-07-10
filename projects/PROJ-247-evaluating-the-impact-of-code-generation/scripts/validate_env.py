"""
Environment Configuration Validation Script.

Validates that the .env file exists and contains all required keys
with non-empty values. Used as a pre-flight check before running
the research pipeline.

Usage:
    python scripts/validate_env.py
"""

import os
import sys
import re
from pathlib import Path

# Define required environment variables
REQUIRED_VARS = {
    "GITHUB_TOKEN": "GitHub API token for repository access",
    "DATA_PATH": "Root directory for data artifacts",
    "LOG_PATH": "Directory for log files"
}

def load_env_file(env_path: Path) -> dict:
    """
    Load variables from a .env file into a dictionary.
    Handles comments and basic key=value parsing.
    """
    env_vars = {}
    if not env_path.exists():
        return env_vars

    with open(env_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            # Skip empty lines and comments
            if not line or line.startswith("#"):
                continue
            
            # Split on first '=' only
            if "=" not in line:
                print(f"Warning: Invalid format at line {line_num}: {line}")
                continue
            
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()
            
            # Remove surrounding quotes if present
            if (value.startswith('"') and value.endswith('"')) or \
               (value.startswith("'") and value.endswith("'")):
                value = value[1:-1]
            
            env_vars[key] = value

    return env_vars

def validate_paths(env_vars: dict) -> bool:
    """
    Validates that path variables point to existing or creatable directories.
    Returns True if valid, False otherwise.
    """
    valid = True
    path_keys = ["DATA_PATH", "LOG_PATH"]
    
    for key in path_keys:
        if key not in env_vars or not env_vars[key]:
            continue
        
        path_val = env_vars[key]
        resolved_path = Path(path_val)
        
        # If it's a relative path, resolve relative to project root
        if not resolved_path.is_absolute():
            resolved_path = Path.cwd() / resolved_path
        
        if not resolved_path.exists():
            print(f"  ⚠ Path does not exist: {resolved_path}")
            # Try to create it (optional, but good practice)
            try:
                resolved_path.mkdir(parents=True, exist_ok=True)
                print(f"    -> Created directory: {resolved_path}")
            except OSError as e:
                print(f"    ✗ Failed to create directory: {e}")
                valid = False
        else:
            if not resolved_path.is_dir():
                print(f"  ✗ Path exists but is not a directory: {resolved_path}")
                valid = False
            else:
                # Check write permissions
                if not os.access(resolved_path, os.W_OK):
                    print(f"  ✗ No write permission for: {resolved_path}")
                    valid = False
                else:
                    print(f"  ✓ Path valid and writable: {resolved_path}")
    
    return valid

def main():
    """Main validation entry point."""
    project_root = Path.cwd()
    env_file = project_root / ".env"
    env_example = project_root / ".env.example"

    print("🔍 Environment Configuration Validation")
    print("-" * 40)

    # Check if .env file exists
    if not env_file.exists():
        print(f"❌ Error: .env file not found at {env_file}")
        print(f"   Please copy .env.example to .env and fill in the values.")
        sys.exit(1)

    # Load .env file
    env_vars = load_env_file(env_file)
    
    # Check for required keys
    missing_keys = []
    empty_keys = []

    for key, description in REQUIRED_VARS.items():
        if key not in env_vars:
            missing_keys.append(key)
        elif not env_vars[key]:
            empty_keys.append(key)

    if missing_keys:
        print(f"❌ Missing required keys: {', '.join(missing_keys)}")
        print(f"   Please ensure .env contains these keys.")
        sys.exit(1)

    if empty_keys:
        print(f"❌ Empty values for keys: {', '.join(empty_keys)}")
        print(f"   Please provide non-empty values for these keys.")
        sys.exit(1)

    print("✓ All required keys present and non-empty")
    
    # Validate GITHUB_TOKEN format (basic check)
    if env_vars.get("GITHUB_TOKEN"):
        token = env_vars["GITHUB_TOKEN"]
        if len(token) < 10:
            print(f"⚠ Warning: GITHUB_TOKEN looks suspiciously short")
        else:
            print("✓ GITHUB_TOKEN format looks valid")

    # Validate paths
    print("Validating paths...")
    paths_valid = validate_paths(env_vars)

    print("-" * 40)
    if paths_valid:
        print("✅ Environment configuration is valid.")
        sys.exit(0)
    else:
        print("❌ Environment configuration has path errors.")
        sys.exit(1)

if __name__ == "__main__":
    main()