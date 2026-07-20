"""
Utility to ensure linting, formatting, and type-checking tools are installed
and configured for the project.
"""
import subprocess
import sys
import os
from pathlib import Path

REQUIRED_TOOLS = [
    ("flake8", "flake8"),
    ("black", "black"),
    ("isort", "isort"),
    ("mypy", "mypy"),
]

CONFIG_FILES = [
    ".flake8",
    "pyproject.toml",
    "mypy.ini",
]

def run_command(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run a shell command and return the result."""
    return subprocess.run(cmd, check=check)

def ensure_config_files_exist(project_root: Path) -> None:
    """Ensure configuration files exist in the project root."""
    missing = []
    for filename in CONFIG_FILES:
        if not (project_root / filename).exists():
            missing.append(filename)
    
    if missing:
        raise FileNotFoundError(
            f"Configuration files missing in project root {project_root}: {missing}. "
            "Please ensure .flake8, pyproject.toml, and mypy.ini are present."
        )

def install_tools() -> None:
    """Install required linting, formatting, and type-checking tools."""
    print("Checking and installing required tools...")
    for package, _ in REQUIRED_TOOLS:
        try:
            __import__(package.replace("-", "_"))
            print(f"  ✓ {package} is already installed")
        except ImportError:
            print(f"  Installing {package}...")
            run_command([sys.executable, "-m", "pip", "install", package])
    print("All tools installed successfully.")

def main() -> None:
    """Main entry point for tooling setup."""
    project_root = Path(__file__).resolve().parent.parent.parent
    print(f"Project root: {project_root}")

    # Ensure config files exist
    try:
        ensure_config_files_exist(project_root)
        print("Configuration files verified.")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Ensure tools are installed
    install_tools()

    print("\nTooling setup complete. You can now run:")
    print("  - black code/ tests/            # Format code")
    print("  - isort code/ tests/            # Sort imports")
    print("  - flake8 code/ tests/           # Lint code")
    print("  - mypy code/ tests/             # Type check code")

if __name__ == "__main__":
    main()
