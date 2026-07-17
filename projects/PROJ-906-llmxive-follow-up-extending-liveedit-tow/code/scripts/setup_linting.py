import subprocess
import sys
import os
import tomli
from pathlib import Path

def check_tool_installed(tool_name: str) -> bool:
    """Check if a tool is installed and accessible."""
    try:
        result = subprocess.run(
            [tool_name, "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"{tool_name} found: {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print(f"{tool_name} not found. Please install it via pip.")
        return False

def verify_config() -> bool:
    """Verify that ruff and black configurations exist and are valid."""
    project_root = Path(__file__).parent.parent.parent
    pyproject_path = project_root / "pyproject.toml"

    if not pyproject_path.exists():
        print("ERROR: pyproject.toml not found in project root.")
        return False

    try:
        with open(pyproject_path, "rb") as f:
            config = tomli.load(f)

        # Check for Ruff config
        if "tool" not in config or "ruff" not in config["tool"]:
            print("ERROR: [tool.ruff] section missing from pyproject.toml")
            return False
        print("✓ [tool.ruff] configuration found.")

        # Check for Black config
        if "tool" not in config or "black" not in config["tool"]:
            print("ERROR: [tool.black] section missing from pyproject.toml")
            return False
        print("✓ [tool.black] configuration found.")

        return True
    except Exception as e:
        print(f"ERROR: Failed to parse pyproject.toml: {e}")
        return False

def main():
    """Main entry point for linting setup verification."""
    print("=== Verifying Linting and Formatting Setup ===")

    # 1. Check tool installation
    ruff_ok = check_tool_installed("ruff")
    black_ok = check_tool_installed("black")

    if not (ruff_ok and black_ok):
        print("\nFailed: Missing required tools.")
        sys.exit(1)

    # 2. Verify configuration
    if not verify_config():
        print("\nFailed: Configuration verification failed.")
        sys.exit(1)

    # 3. Run actual checks
    print("\n--- Running `ruff check .` ---")
    try:
        result = subprocess.run(
            ["ruff", "check", "."],
            check=True,
            capture_output=False
        )
        print("✓ Ruff check passed.")
    except subprocess.CalledProcessError as e:
        print(f"✗ Ruff check failed with exit code {e.returncode}")
        sys.exit(1)

    print("\n--- Running `black --check .` ---")
    try:
        result = subprocess.run(
            ["black", "--check", "."],
            check=True,
            capture_output=False
        )
        print("✓ Black check passed.")
    except subprocess.CalledProcessError as e:
        print(f"✗ Black check failed with exit code {e.returncode}")
        sys.exit(1)

    print("\n=== All linting and formatting checks passed! ===")

if __name__ == "__main__":
    main()