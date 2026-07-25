import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run a shell command and return the result."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, check=check)
    return result

def create_ruff_config(project_root: Path) -> None:
    """Create a .ruff.toml configuration file."""
    config_content = """
    [lint]
    select = [
        "E",  # pycodestyle errors
        "W",  # pycodestyle warnings
        "F",  # Pyflakes
        "I",  # isort
        "C",  # flake8-comprehensions
        "B",  # flake8-bugbear
    ]
    ignore = [
        "E501", # line too long (handled by black)
        "B008", # do not perform function calls in argument defaults
        "C901", # too complex
    ]

    [lint.per-file-ignores]
    "tests/*" = ["S101"] # assert allowed in tests

    [lint.isort]
    known-first-party = ["models", "utils"]

    [format]
    line-length = 88
    """
    config_path = project_root / ".ruff.toml"
    with open(config_path, "w") as f:
        f.write(config_content)
    print(f"Created {config_path}")

def create_black_config(project_root: Path) -> None:
    """Create a pyproject.toml with Black configuration if not present, or append."""
    config_path = project_root / "pyproject.toml"
    
    black_section = """
    [tool.black]
    line-length = 88
    target-version = ['py311']
    include = '\\.pyi?$'
    exclude = '''
    /(
        \\.git
      | \\.hg
      | \\.mypy_cache
      | \\.tox
      | \\.venv
      | _build
      | buck-out
      | build
      | dist
    )/
    '''
    """

    if config_path.exists():
        with open(config_path, "r") as f:
            content = f.read()
        if "[tool.black]" in content:
            print("Black configuration already exists in pyproject.toml")
            return
        with open(config_path, "a") as f:
            f.write("\n" + black_section)
    else:
        with open(config_path, "w") as f:
            f.write(black_section)
    print(f"Updated {config_path} with Black configuration")

def main() -> None:
    """Main entry point to setup linting and formatting."""
    project_root = Path(__file__).resolve().parent.parent
    
    print("Setting up linting and formatting tools...")

    # Install dependencies if not present
    try:
        run_command([sys.executable, "-m", "pip", "install", "-q", "ruff", "black"])
    except subprocess.CalledProcessError as e:
        print(f"Warning: Failed to install tools automatically: {e}")
        print("Please install manually: pip install ruff black")
        return

    # Create configuration files
    create_ruff_config(project_root)
    create_black_config(project_root)

    # Verify installation by running --version
    try:
        run_command(["ruff", "--version"])
        run_command(["black", "--version"])
    except subprocess.CalledProcessError as e:
        print(f"Error: Could not verify tool installation: {e}")
        return

    print("Linting and formatting setup complete.")
    print("To run linter: ruff check .")
    print("To run formatter: black .")
    print("To run both: ruff check . && black .")

if __name__ == "__main__":
    main()
