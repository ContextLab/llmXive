"""
Script to verify and optionally install linting tools (ruff, black).
This script is used during the setup phase to ensure the project
has the necessary tools configured.
"""
import subprocess
import sys
from pathlib import Path

def check_tool(tool_name: str) -> bool:
    """Check if a tool is installed."""
    try:
        subprocess.run(
            [tool_name, "--version"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def install_tool(tool_name: str) -> None:
    """Install a tool using pip."""
    print(f"Installing {tool_name}...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", tool_name])

def main() -> int:
    """Main entry point for linting setup verification."""
    project_root = Path(__file__).parent.parent
    config_files = [
        project_root / "pyproject.toml",
        project_root / ".ruff.toml",
        project_root / ".black.toml",
    ]

    print("Checking linting configuration files...")
    for config in config_files:
        if not config.exists():
            print(f"Error: Missing config file: {config}")
            return 1
        print(f"Found: {config}")

    tools = {"ruff": "ruff", "black": "black"}
    for name, cmd in tools.items():
        if not check_tool(cmd):
            print(f"{name} not found. Attempting to install...")
            try:
                install_tool(cmd)
            except subprocess.CalledProcessError as e:
                print(f"Failed to install {name}: {e}")
                return 1
        else:
            print(f"{name} is installed.")

    # Verify configuration validity
    print("\nVerifying Ruff configuration...")
    try:
        subprocess.run(
            ["ruff", "check", "--config", str(project_root / ".ruff.toml"), "."],
            cwd=project_root,
            check=False, # Don't fail if lint errors exist, just config validity
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        print("Ruff configuration is valid.")
    except FileNotFoundError:
        print("Ruff command not found after installation.")
        return 1

    print("\nVerifying Black configuration...")
    try:
        subprocess.run(
            ["black", "--config", str(project_root / ".black.toml"), "--check", "."],
            cwd=project_root,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        print("Black configuration is valid.")
    except FileNotFoundError:
        print("Black command not found after installation.")
        return 1

    print("\nLinting setup complete.")
    return 0

if __name__ == "__main__":
    sys.exit(main())