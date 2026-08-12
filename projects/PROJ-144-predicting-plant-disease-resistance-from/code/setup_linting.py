"""
Setup script for linting tools (black, flake8, isort, pre-commit).

This script configures the project's linting infrastructure as per T003.
"""

import subprocess
import sys
from pathlib import Path

from utils.constants import PROJECT_ROOT


def install_dependencies():
    """Install linting dependencies."""
    print("Installing linting dependencies...")
    
    dependencies = [
        "black",
        "flake8",
        "isort",
        "pre-commit",
        "yamllint",
    ]
    
    for dep in dependencies:
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", dep],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            print(f"  ✓ Installed {dep}")
        except subprocess.CalledProcessError:
            print(f"  ✗ Failed to install {dep}")
            sys.exit(1)

def setup_pre_commit():
    """Set up pre-commit hooks."""
    print("\nSetting up pre-commit hooks...")
    
    pre_commit_config = PROJECT_ROOT / ".pre-commit-config.yaml"
    
    if not pre_commit_config.exists():
        print("  Creating .pre-commit-config.yaml...")
        config_content = """
repos:
  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
        language_version: python3.11
  - repo: https://github.com/pycqa/flake8
    rev: 7.0.0
    hooks:
      - id: flake8
        args: [--max-line-length=88, --extend-ignore=E203]
  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort
        args: [--profile=black]
  - repo: https://github.com/pre-commit/mirrors-yamllint
    rev: v1.35.1
    hooks:
      - id: yamllint
        args: [-d, '{extends: default, rules: {line-length: disable}}']
"""
        with open(pre_commit_config, "w", encoding="utf-8") as f:
            f.write(config_content.strip())
        print("  ✓ Created .pre-commit-config.yaml")
    else:
        print("  ✓ .pre-commit-config.yaml already exists")
    
    # Initialize pre-commit
    try:
        subprocess.check_call(
            ["pre-commit", "install"],
            cwd=PROJECT_ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        print("  ✓ Pre-commit hooks installed")
    except subprocess.CalledProcessError:
        print("  ✗ Failed to install pre-commit hooks")
        sys.exit(1)

def create_linting_config_files():
    """Create configuration files for linting tools."""
    print("\nCreating linting configuration files...")
    
    # .flake8
    flake8_config = PROJECT_ROOT / ".flake8"
    if not flake8_config.exists():
        content = """
[flake8]
max-line-length = 88
extend-ignore = E203
exclude = 
    .git,
    __pycache__,
    .venv,
    build,
    dist
per-file-ignores =
    __init__.py:F401
"""
        with open(flake8_config, "w", encoding="utf-8") as f:
            f.write(content.strip())
        print("  ✓ Created .flake8")
    else:
        print("  ✓ .flake8 already exists")
    
    # pyproject.toml for isort/black
    pyproject = PROJECT_ROOT / "pyproject.toml"
    if not pyproject.exists():
        content = """
[tool.black]
line-length = 88
target-version = ['py311']
include = '\\.pyi?$'
exclude = '''
(
  /(
      \.git
    | \.hg
    | \.mypy_cache
    | \.tox
    | \.venv
    | _build
    | buck-out
    | build
    | dist
  )/
)
'''

[tool.isort]
profile = "black"
line_length = 88
"""
        with open(pyproject, "w", encoding="utf-8") as f:
            f.write(content.strip())
        print("  ✓ Created pyproject.toml")
    else:
        print("  ✓ pyproject.toml already exists")

def run_initial_lint_check():
    """Run initial lint check to identify issues."""
    print("\nRunning initial lint check...")
    
    try:
        # Run black check
        result = subprocess.run(
            ["black", "--check", "code/"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print("  ℹ Black issues found (will be fixed by pre-commit)")
        else:
            print("  ✓ Black check passed")
    except FileNotFoundError:
        print("  ✗ Black not found (install with pip install black)")
    
    try:
        # Run flake8
        result = subprocess.run(
            ["flake8", "code/"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print("  ℹ Flake8 issues found (see output above)")
        else:
            print("  ✓ Flake8 check passed")
    except FileNotFoundError:
        print("  ✗ Flake8 not found (install with pip install flake8)")

def main():
    """Main entry point for the setup script."""
    print("=" * 60)
    print("Setting up linting infrastructure")
    print("=" * 60)
    
    install_dependencies()
    setup_pre_commit()
    create_linting_config_files()
    run_initial_lint_check()
    
    print("\n" + "=" * 60)
    print("Linting setup complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Run 'pre-commit run --all-files' to fix all issues")
    print("  2. Run 'python code/refactor_linting_fixes.py' for additional cleanup")
    print("  3. Verify with 'black --check code/' and 'flake8 code/'")

if __name__ == "__main__":
    main()