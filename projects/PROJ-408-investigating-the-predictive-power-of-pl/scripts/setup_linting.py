"""
Script to verify linting and formatting tool configuration.
This script checks if ruff and black are installed and if the configuration
files (pyproject.toml) are correctly set up to enforce specific error codes.

It does not perform the linting itself (that is done via CLI), but validates
the presence of the configuration required by T003.
"""
import sys
import subprocess
import tomli
from pathlib import Path

def check_tool_installed(tool_name: str) -> bool:
    """Check if a tool is installed and available in PATH."""
    try:
        subprocess.run(
            [tool_name, "--version"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def verify_ruff_config() -> bool:
    """Verify that ruff configuration enforces required error codes."""
    config_path = Path("pyproject.toml")
    if not config_path.exists():
        print("ERROR: pyproject.toml not found.")
        return False

    try:
        with open(config_path, "rb") as f:
            config = tomli.load(f)
        
        ruff_config = config.get("tool", {}).get("ruff", {}).get("lint", {})
        select_list = ruff_config.get("select", [])
        
        required_codes = {"F401", "E402"} # Unused imports, import not at top
        
        missing_codes = required_codes - set(select_list)
        
        if missing_codes:
            print(f"ERROR: Missing required error codes in ruff config: {missing_codes}")
            print(f"Current select list: {select_list}")
            return False
        
        print("SUCCESS: Ruff configuration enforces required error codes.")
        return True
    except Exception as e:
        print(f"ERROR: Failed to parse pyproject.toml: {e}")
        return False

def main():
    print("Verifying Linting and Formatting Configuration (T003)...")
    
    # Check tools
    ruff_ok = check_tool_installed("ruff")
    black_ok = check_tool_installed("black")
    
    if not ruff_ok:
        print("ERROR: 'ruff' is not installed or not in PATH.")
    else:
        print("SUCCESS: 'ruff' is installed.")
        
    if not black_ok:
        print("ERROR: 'black' is not installed or not in PATH.")
    else:
        print("SUCCESS: 'black' is installed.")
    
    # Verify config
    config_ok = verify_ruff_config()
    
    if ruff_ok and black_ok and config_ok:
        print("\nAll checks passed. T003 configuration is valid.")
        return 0
    else:
        print("\nSome checks failed. Please install missing tools or update pyproject.toml.")
        return 1

if __name__ == "__main__":
    sys.exit(main())