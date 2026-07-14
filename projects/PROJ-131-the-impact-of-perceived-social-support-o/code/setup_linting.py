import os
import subprocess
import sys
from pathlib import Path

import tomlkit

def check_tool_installed(tool_name: str) -> bool:
    """Check if a tool is installed in the current environment."""
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "show", tool_name],
            check=True,
            capture_output=True,
            text=True,
        )
        return True
    except subprocess.CalledProcessError:
        return False

def install_tool(tool_name: str) -> bool:
    """Install a tool if it is not already installed."""
    if check_tool_installed(tool_name):
        print(f"{tool_name} is already installed.")
        return True
    print(f"Installing {tool_name}...")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", tool_name], check=True
        )
        return True
    except subprocess.CalledProcessError:
        print(f"Failed to install {tool_name}.")
        return False

def verify_config_files() -> bool:
    """Verify that configuration files exist or can be created."""
    return True  # We will create them if they don't exist

def create_ruff_config() -> None:
    """Create a default ruff configuration file."""
    config_path = Path("ruff.toml")
    if config_path.exists():
        print(f"ruff.toml already exists at {config_path}")
        return

    config_content = """
# Ruff configuration
lint.select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # Pyflakes
    "I",  # isort
    "B",  # flake8-bugbear
    "C4", # flake8-comprehensions
    "UP", # pyupgrade
]
lint.ignore = [
    "E501", # Line too long (handled by black)
    "B008", # Do not perform function call in argument defaults
]

[lint.per-file-ignores]
"tests/*" = ["S101"] # Allow assert in tests

[lint.isort]
known-first-party = ["data", "analysis", "logger"]
"""
    with open(config_path, "w") as f:
        f.write(config_content)
    print(f"Created ruff.toml at {config_path}")

def create_black_config() -> None:
    """Create a default black configuration in pyproject.toml."""
    config_path = Path("pyproject.toml")
    if not config_path.exists():
        # Create a minimal pyproject.toml if it doesn't exist
        with open(config_path, "w") as f:
            f.write("[build-system]\nrequires = [\"setuptools\"]\n")

    # Parse existing content
    with open(config_path, "r") as f:
        content = f.read()

    try:
        doc = tomlkit.parse(content)
    except Exception:
        doc = tomlkit.document()
        doc.add(tomlkit.table("build-system"))
        doc["build-system"]["requires"] = ["setuptools"]

    # Ensure tool.black section exists
    if "tool" not in doc:
        doc["tool"] = tomlkit.table()
    if "black" not in doc["tool"]:
        doc["tool"]["black"] = tomlkit.table()

    doc["tool"]["black"]["line-length"] = 88
    doc["tool"]["black"]["target-version"] = ["py311"]
    doc["tool"]["black"]["skip-string-normalization"] = False

    with open(config_path, "w") as f:
        f.write(tomlkit.dumps(doc))
    print(f"Updated pyproject.toml with Black configuration at {config_path}")

def main() -> None:
    """Main entry point for setting up linting and formatting tools."""
    print("Setting up linting (ruff) and formatting (black) tools...")

    # Install tools
    ruff_installed = install_tool("ruff")
    black_installed = install_tool("black")

    if not ruff_installed or not black_installed:
        print("Failed to install required tools. Exiting.")
        sys.exit(1)

    # Create configuration files
    create_ruff_config()
    create_black_config()

    print("Linting and formatting tools configured successfully.")
    print("You can now run:")
    print("  ruff check .       # to lint")
    print("  black .            # to format")
    print("  ruff check . && black . --check  # to check both")

if __name__ == "__main__":
    main()