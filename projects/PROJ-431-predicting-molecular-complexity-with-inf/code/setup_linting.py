"""
Linting and formatting configuration setup script.

This script initializes the project's linting (flake8) and formatting (black)
configuration files and installs the necessary dependencies.
"""
import subprocess
import sys
import os
from pathlib import Path


def run_command(cmd: list, description: str) -> bool:
    """Run a shell command and return True if successful."""
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}", file=sys.stderr)
        if e.stderr:
            print(e.stderr, file=sys.stderr)
        return False


def main():
    """Main entry point for setting up linting and formatting."""
    print("Setting up linting (flake8) and formatting (black)...")

    # Ensure we are in the project root
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    # Install dependencies
    print("\n1. Installing flake8 and black...")
    if not run_command(
        [sys.executable, "-m", "pip", "install", "flake8", "black"],
        "Installing flake8 and black"
    ):
        print("Failed to install dependencies. Exiting.")
        return 1

    # Create .flake8 configuration
    print("\n2. Creating .flake8 configuration file...")
    flake8_config = project_root / ".flake8"
    flake8_content = """[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude =
    .git,
    __pycache__,
    build,
    dist,
    .eggs,
    *.egg-info,
    .venv,
    venv
max-complexity = 10
"""
    flake8_config.write_text(flake8_content)
    print(f"Created {flake8_config}")

    # Create pyproject.toml with black configuration
    print("\n3. Creating pyproject.toml with black configuration...")
    pyproject_config = project_root / "pyproject.toml"
    # Check if file exists and has content
    if pyproject_config.exists():
        content = pyproject_config.read_text()
        if "[tool.black]" in content:
            print(f"{pyproject_config} already contains black configuration. Skipping.")
        else:
            # Append black configuration
            black_section = """
[tool.black]
line-length = 88
target-version = ['py38', 'py39', 'py310', 'py311']
include = '\\.pyi?$'
extend-exclude = '''
/(
    \\.#
    | .git
    | __pycache__
    | build
    | dist
    | .eggs
    | *.egg-info
    | .venv
    | venv
)/
'''
"""
            pyproject_config.write_text(content + black_section)
            print(f"Appended black configuration to {pyproject_config}")
    else:
        black_content = """[tool.black]
line-length = 88
target-version = ['py38', 'py39', 'py310', 'py311']
include = '\\.pyi?$'
extend-exclude = '''
/(
    \\.#
    | .git
    | __pycache__
    | build
    | dist
    | .eggs
    | *.egg-info
    | .venv
    | venv
)/
'''
"""
        pyproject_config.write_text(black_content)
        print(f"Created {pyproject_config} with black configuration")

    # Create .gitignore entry if needed
    print("\n4. Checking .gitignore for linting artifacts...")
    gitignore_path = project_root / ".gitignore"
    linting_entries = [
        "# Linting and formatting artifacts",
        ".coverage",
        "htmlcov/",
        ".mypy_cache/",
        ".pytest_cache/",
        ".ruff_cache/",
    ]
    if gitignore_path.exists():
        existing = gitignore_path.read_text()
        for entry in linting_entries:
            if entry not in existing:
                with open(gitignore_path, "a") as f:
                    f.write("\n" + entry + "\n")
    else:
        with open(gitignore_path, "w") as f:
            f.write("\n".join(linting_entries) + "\n")
    print(f"Updated {gitignore_path}")

    print("\nLinting and formatting setup complete!")
    print("\nTo run linter: flake8 code/ tests/")
    print("To run formatter: black code/ tests/")
    return 0


if __name__ == "__main__":
    sys.exit(main())