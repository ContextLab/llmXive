"""
Setup script for linting and formatting tools.
Verifies ruff and black are installed and configuration files exist.
"""
import subprocess
import sys
from pathlib import Path

def check_tool(tool_name: str) -> bool:
    """Check if a tool is installed and available."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", tool_name, "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"✓ {tool_name} is installed: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError:
        print(f"✗ {tool_name} is not installed or not in PATH.")
        return False

def check_config_files() -> bool:
    """Check if configuration files exist in the code directory."""
    config_files = ["pyproject.toml", ".ruff.toml", ".black.toml"]
    code_dir = Path(__file__).parent
    all_exist = True

    for config_file in config_files:
        file_path = code_dir / config_file
        if file_path.exists():
            print(f"✓ Configuration file found: {config_file}")
        else:
            print(f"✗ Configuration file missing: {config_file}")
            all_exist = False

    return all_exist

def main():
    """Main entry point for setup_linting."""
    print("Checking linting and formatting setup...")
    print("-" * 40)

    tools_ok = True
    for tool in ["black", "ruff"]:
        if not check_tool(tool):
            tools_ok = False

    print("-" * 40)
    config_ok = check_config_files()

    print("-" * 40)
    if tools_ok and config_ok:
        print("✓ Linting and formatting setup is complete.")
        return 0
    else:
        print("✗ Setup incomplete. Please install missing tools or add config files.")
        if not tools_ok:
            print("  To install tools, run: pip install black ruff")
        return 1

if __name__ == "__main__":
    sys.exit(main())