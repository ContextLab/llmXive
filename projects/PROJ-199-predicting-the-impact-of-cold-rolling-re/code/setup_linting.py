"""
Setup linting and formatting tools for the project.

This script configures flake8, black, and pre-commit hooks to ensure
code quality and consistency across the project.
"""
import subprocess
import sys
import os
from pathlib import Path
import tomli_w
import tomli


def run_command(cmd: list, check: bool = True) -> subprocess.CompletedProcess:
    """
    Run a shell command and return the result.
    
    Args:
        cmd: Command and arguments as a list
        check: If True, raise CalledProcessError on non-zero exit
        
    Returns:
        CompletedProcess instance
    """
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, check=check)
    return result


def create_flake8_config() -> None:
    """
    Create a .flake8 configuration file with project-specific settings.
    """
    config_content = """[flake8]
# Maximum line length
max-line-length = 88

# Extensions to ignore
extend-ignore = E203, E501, W503

# Exclude directories
exclude = 
    .git,
    __pycache__,
    .eggs,
    *.egg-info,
    build,
    dist,
    .venv,
    venv

# Per-file ignores
per-file-ignores =
    # Allow longer lines in test files for readability
    tests/*: E501

# Maximum complexity for cyclomatic complexity
max-complexity = 10
"""
    path = Path(".flake8")
    path.write_text(config_content)
    print(f"Created {path}")


def create_pyproject_toml() -> None:
    """
    Create or update pyproject.toml with black and tool configurations.
    """
    pyproject_path = Path("pyproject.toml")
    
    # Read existing content if it exists
    if pyproject_path.exists():
        with open(pyproject_path, "rb") as f:
            try:
                config = tomli.load(f)
            except tomli.TOMLDecodeError:
                config = {}
    else:
        config = {}
    
    # Ensure [tool.black] section exists
    if "tool" not in config:
        config["tool"] = {}
    
    black_config = {
        "line-length": 88,
        "target-version": ["py39", "py310", "py311"],
        "include": r"\.pyi?$",
        "exclude": r"""
            (
                \.git
                | \.hg
                | \.mypy_cache
                | \.tox
                | \.venv
                | _build
                | buck-out
                | build
                | dist
                | \.eggs
                | \.egg-info
            )/
        """,
    }
    config["tool"]["black"] = black_config
    
    # Ensure [tool.isort] section exists (for compatibility)
    isort_config = {
        "profile": "black",
        "line_length": 88,
        "skip_glob": [
            "*/.git/*",
            "*/__pycache__/*",
            "*/.eggs/*",
            "*/build/*",
            "*/dist/*",
            "*/.venv/*",
        ],
    }
    config["tool"]["isort"] = isort_config
    
    # Write updated config
    with open(pyproject_path, "w", encoding="utf-8") as f:
        tomli_w.dump(config, f)
    
    print(f"Updated {pyproject_path}")


def install_dev_dependencies() -> None:
    """
    Install development dependencies for linting and formatting.
    """
    dev_packages = [
        "flake8",
        "black",
        "pre-commit",
        "isort",
        "pytest",
        "pytest-cov",
    ]
    
    print("Installing development dependencies...")
    run_command([sys.executable, "-m", "pip", "install", "-U"] + dev_packages)
    print("Development dependencies installed successfully.")


def setup_pre_commit() -> None:
    """
    Initialize pre-commit hooks and create configuration file.
    """
    pre_commit_path = Path(".pre-commit-config.yaml")
    
    config_content = """repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
- id: trailing-whitespace
- id: end-of-file-fixer
- id: check-yaml
- id: check-added-large-files
- id: check-merge-conflict
- id: debug-statements

  - repo: https://github.com/psf/black
    rev: 24.3.0
    hooks:
- id: black
  language_version: python3

  - repo: https://github.com/pycqa/flake8
    rev: 7.0.0
    hooks:
- id: flake8
  additional_dependencies: []

  - repo: https://github.com/PyCQA/isort
    rev: 5.13.2
    hooks:
- id: isort
  name: isort (python)
"""
    
    pre_commit_path.write_text(config_content)
    print(f"Created {pre_commit_path}")
    
    # Initialize pre-commit if not already installed
    if not Path(".git").exists():
        print("Initializing git repository for pre-commit...")
        run_command(["git", "init"])
    
    # Install pre-commit hooks
    print("Installing pre-commit hooks...")
    run_command(["pre-commit", "install"])
    print("Pre-commit hooks installed successfully.")


def main() -> None:
    """
    Main entry point for setting up linting and formatting tools.
    """
    print("=" * 60)
    print("Setting up linting and formatting tools")
    print("=" * 60)
    
    # Create configuration files
    create_flake8_config()
    create_pyproject_toml()
    
    # Install development dependencies
    install_dev_dependencies()
    
    # Setup pre-commit hooks
    setup_pre_commit()
    
    print("=" * 60)
    print("Linting and formatting setup complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Run 'pre-commit run --all-files' to check all files")
    print("2. Run 'black code/' to format code")
    print("3. Run 'flake8 code/' to check for linting issues")
    print("4. Commit your changes to activate pre-commit hooks")


if __name__ == "__main__":
    main()