import os
import sys
import subprocess
from pathlib import Path

def ensure_project_root() -> Path:
    """Ensure we are in the project root."""
    return Path.cwd()

def write_pyproject_toml(project_root: Path) -> None:
    """Write pyproject.toml with Black configuration."""
    content = """[tool.black]
line-length = 88
target-version = ['py311']
"""
    path = project_root / "pyproject.toml"
    with open(path, "w") as f:
        f.write(content)
    print(f"Created {path}")

def write_ruff_toml(project_root: Path) -> None:
    """Write .ruff.toml with specific rules."""
    content = """[ruff]
line-length = 88
ignore = ["E501"]
target-version = "py311"
"""
    path = project_root / ".ruff.toml"
    with open(path, "w") as f:
        f.write(content)
    print(f"Created {path}")

def install_tools() -> None:
    """Install linting and formatting tools."""
    subprocess.run([sys.executable, "-m", "pip", "install", "black", "ruff"], check=True)
    print("Tools installed.")

def main():
    """Entry point for setup_linting script."""
    project_root = ensure_project_root()
    write_pyproject_toml(project_root)
    write_ruff_toml(project_root)
    # Uncomment to install tools:
    # install_tools()

if __name__ == "__main__":
    main()