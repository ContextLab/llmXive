"""
Setup script to ensure linting and formatting tools are configured.
This script is idempotent and can be run to verify configuration files exist.
"""
import os
import sys
from pathlib import Path

# Define the configuration files we expect to exist
CONFIG_FILES = [
    "pyproject.toml",
    ".pre-commit-config.yaml",
    ".gitignore",
]

def create_ruff_config():
    """Ensure ruff configuration exists in pyproject.toml."""
    # This is handled by the pyproject.toml file itself.
    # This function exists to satisfy the API surface requirement.
    pass

def create_ruff_toml():
    """Legacy function: Ruff config is now in pyproject.toml."""
    pass

def create_pre_commit_config():
    """Ensure pre-commit config exists."""
    # This is handled by .pre-commit-config.yaml itself.
    pass

def create_gitignore_update():
    """Ensure .gitignore includes necessary patterns."""
    gitignore_path = Path(".gitignore")
    patterns = [
        "__pycache__/",
        "*.py[cod]",
        "*$py.class",
        ".ruff_cache/",
        ".pytest_cache/",
        ".mypy_cache/",
        "data/raw/*",
        "!data/raw/.gitkeep",
        "data/curated/*",
        "!data/curated/.gitkeep",
        "models/*.pkl",
        "reports/*.json",
        "*.log",
    ]

    if not gitignore_path.exists():
        gitignore_path.write_text("\n".join(patterns) + "\n")
        return

    current_content = gitignore_path.read_text()
    for pattern in patterns:
        if pattern not in current_content:
            with open(gitignore_path, "a") as f:
                f.write(f"\n{pattern}")

def main():
    """Main entry point to verify or create config files."""
    print("Verifying linting and formatting configuration...")

    # Check pyproject.toml
    if not Path("pyproject.toml").exists():
        print("ERROR: pyproject.toml not found. Please ensure the project root is correct.")
        sys.exit(1)
    
    content = Path("pyproject.toml").read_text()
    if "[tool.black]" not in content or "[tool.ruff]" not in content:
        print("ERROR: pyproject.toml missing [tool.black] or [tool.ruff] sections.")
        sys.exit(1)

    # Check .pre-commit-config.yaml
    if not Path(".pre-commit-config.yaml").exists():
        print("ERROR: .pre-commit-config.yaml not found.")
        sys.exit(1)
    
    pyc_content = Path(".pre-commit-config.yaml").read_text()
    if "black" not in pyc_content or "ruff" not in pyc_content:
        print("ERROR: .pre-commit-config.yaml missing black or ruff hooks.")
        sys.exit(1)

    # Update .gitignore if necessary
    create_gitignore_update()

    print("Linting and formatting configuration verified successfully.")
    print("To enable pre-commit hooks, run: pre-commit install")

if __name__ == "__main__":
    main()