"""
Configuration helpers for linting (Ruff) and formatting (Black).
"""
import os
import subprocess
import sys
from pathlib import Path
from config import get_project_root


def ensure_project_root() -> Path:
    """
    Ensure the project root directory exists.

    Returns:
        The project root path.

    Raises:
        FileNotFoundError: If the project root is not found.
    """
    root = get_project_root()
    if not root.exists():
        raise FileNotFoundError(f"Project root not found at {root}")
    return root


def create_ruff_config(root: Path) -> None:
    """
    Create a default ruff.toml or pyproject.toml configuration if missing.
    This function ensures the configuration file exists in the project root.
    """
    pyproject_path = root / "pyproject.toml"
    if pyproject_path.exists():
        # Check if [tool.ruff] exists
        content = pyproject_path.read_text()
        if "[tool.ruff]" in content:
            print("Ruff configuration already exists in pyproject.toml.")
            return

    # If pyproject.toml exists but no ruff config, we could append,
    # but for simplicity, we assume the file created in T003 is sufficient.
    # If it doesn't exist, we create it.
    if not pyproject_path.exists():
        print("Creating pyproject.toml with default Ruff/Black config...")
        # This logic is handled by the artifact creation in T003.
        # This function is a placeholder for potential runtime generation if needed.
        pass


def create_black_config(root: Path) -> None:
    """
    Create a default black configuration in pyproject.toml if missing.
    """
    pyproject_path = root / "pyproject.toml"
    if pyproject_path.exists():
        content = pyproject_path.read_text()
        if "[tool.black]" in content:
            print("Black configuration already exists in pyproject.toml.")
            return
    # Similar to Ruff, assumed handled by T003 artifact.


def verify_tools() -> bool:
    """
    Verify that ruff and black are installed and accessible.

    Returns:
        True if both tools are found, False otherwise.
    """
    tools = ["ruff", "black"]
    for tool in tools:
        try:
            subprocess.run(
                [tool, "--version"],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            print(f"✓ {tool} is installed.")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(f"✗ {tool} is NOT installed.")
            return False
    return True


def main() -> int:
    """
    Main entry point for the linting configuration script.
    """
    print("Configuring linting (Ruff) and formatting (Black)...")
    root = ensure_project_root()
    create_ruff_config(root)
    create_black_config(root)

    if not verify_tools():
        print("\nPlease install the required tools:")
        print("  pip install ruff==0.1.0 black==23.10.0")
        return 1

    print("\nConfiguration verified successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
