import os
import subprocess
import sys
from pathlib import Path


def check_config_files():
    """Check if ruff and black config files exist in the project root."""
    project_root = Path(__file__).parent.parent
    ruff_config = project_root / "pyproject.toml"
    black_config = project_root / "pyproject.toml"

    if not ruff_config.exists():
        print(f"Warning: {ruff_config} not found. Creating default configuration.")
        return False

    print("Configuration files found.")
    return True


def install_dev_dependencies():
    """Install ruff and black as development dependencies."""
    print("Installing development dependencies (ruff, black)...")
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-U", "ruff", "black"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        print("Dependencies installed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to install dependencies: {e}")
        return False


def initialize_pre_commit():
    """Initialize pre-commit configuration if not present."""
    project_root = Path(__file__).parent.parent
    pre_commit_config = project_root / ".pre-commit-config.yaml"

    if pre_commit_config.exists():
        print(".pre-commit-config.yaml already exists.")
        return True

    print("Creating .pre-commit-config.yaml...")
    config_content = """repos:
  - repo: https://github.com/psf/black
    rev: 24.2.0
    hooks:
- id: black
  language_version: python3
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.3.0
    hooks:
- id: ruff
  args: [--fix, --exit-non-zero-on-fix]
- id: ruff-format
"""
    try:
        pre_commit_config.write_text(config_content)
        print("Created .pre-commit-config.yaml.")
        return True
    except IOError as e:
        print(f"Failed to create pre-commit config: {e}")
        return False


def run_linter():
    """Run ruff linter on the codebase."""
    project_root = Path(__file__).parent.parent
    print("Running ruff linter...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "check", str(project_root / "code")],
            cwd=project_root,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("Linter passed: No issues found.")
            return True
        else:
            print("Linter found issues:")
            print(result.stdout)
            return False
    except FileNotFoundError:
        print("Error: ruff not found. Please install it first.")
        return False


def run_formatter():
    """Run black formatter on the codebase."""
    project_root = Path(__file__).parent.parent
    print("Running black formatter...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "black", "--check", str(project_root / "code")],
            cwd=project_root,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("Formatter passed: Code is already formatted.")
            return True
        else:
            print("Formatter found formatting issues.")
            print("Run 'black code/' to fix them.")
            return False
    except FileNotFoundError:
        print("Error: black not found. Please install it first.")
        return False


def main():
    """Main entry point for setting up linting and formatting tools."""
    print("Setting up linting and formatting tools...")

    # Check configuration
    if not check_config_files():
        print("Creating default configuration in pyproject.toml...")
        project_root = Path(__file__).parent.parent
        pyproject = project_root / "pyproject.toml"
        if pyproject.exists():
            content = pyproject.read_text()
            # Append ruff and black configs if not present
            if "[tool.ruff]" not in content:
                content += "\n[tool.ruff]\nline-length = 88\nselect = [\"E\", \"F\", \"W\", \"I\"]\n"
            if "[tool.black]" not in content:
                content += "\n[tool.black]\nline-length = 88\ntarget-version = ['py38']\n"
            pyproject.write_text(content)
        else:
            content = """[tool.ruff]
line-length = 88
select = ["E", "F", "W", "I"]

[tool.black]
line-length = 88
target-version = ['py38']
"""
            pyproject.write_text(content)

    # Install dependencies
    if not install_dev_dependencies():
        print("Failed to install dependencies. Exiting.")
        sys.exit(1)

    # Initialize pre-commit
    initialize_pre_commit()

    print("\nSetup complete. Run 'ruff check code/' and 'black --check code/' to verify.")


if __name__ == "__main__":
    main()