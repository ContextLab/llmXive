import os
import subprocess
import sys
from pathlib import Path

def write_config_file():
    """Creates or updates pyproject.toml and .ruff.toml with linting configurations."""
    root = Path(__file__).parent.parent
    
    pyproject_content = """[build-system]
requires = ["setuptools>=42", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "llm-carbon-footprint"
version = "0.1.0"
description = "Measuring the Carbon Footprint of LLM-Assisted Code Generation"
requires-python = ">=3.9"
dependencies = [
    "transformers",
    "codecarbon",
    "datasets",
    "scikit-learn",
    "pandas",
    "matplotlib",
    "seaborn",
    "torch",
]

[tool.black]
line-length = 88
target-version = ['py39']
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

def setup_ruff_config() -> Path:
    """Create or update pyproject.toml with Ruff configuration."""
    pyproject_path = Path("pyproject.toml")
    
    if pyproject_path.exists():
        content = pyproject_path.read_text(encoding="utf-8")
        if "[tool.ruff]" in content:
            return pyproject_path
    else:
        content = ""

    ruff_config = """
[tool.ruff]
line-length = 88
target-version = "py39"
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # pyflakes
    "I",  # isort
    "C",  # flake8-comprehensions
    "B",  # flake8-bugbear
]
ignore = [
    "E501",  # line too long, handled by black
    "B008",  # do not perform function calls in argument defaults
    "C901",  # too complex
]

[tool.ruff.per-file-ignores]
"__init__.py" = ["F401"]

[tool.ruff.isort]
known-first-party = ["code"]
force-sort-within-sections = true
"""
    if "[tool.ruff]" not in content:
        content += ruff_config
        pyproject_path.write_text(content, encoding="utf-8")
    
    return pyproject_path

    ruff_content = """# Ruff configuration file (alternative to pyproject.toml)
# This file is used if ruff is invoked with --config=.ruff.toml
# or if pyproject.toml is not present in the project root.

line-length = 88
target-version = "py39"

[lint]
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # pyflakes
    "I",  # isort
    "C",  # flake8-comprehensions
    "B",  # flake8-bugbear
]
ignore = [
    "E501",  # line too long, handled by black
    "B008",  # do not perform function calls in argument defaults
    "C901",  # too complex
]

[lint.isort]
known-first-party = ["code"]
force-sort-within-sections = true
"""

    pyproject_path = root / "pyproject.toml"
    ruff_path = root / ".ruff.toml"

    # Write pyproject.toml
    with open(pyproject_path, 'w', encoding='utf-8') as f:
        f.write(pyproject_content)
    print(f"Updated {pyproject_path} with Black and Ruff configurations.")

    # Write .ruff.toml
    with open(ruff_path, 'w', encoding='utf-8') as f:
        f.write(ruff_content)
    print(f"Updated {ruff_path} with Ruff configuration.")

def setup_black_config():
    """Ensures Black is installed and configured."""
    try:
        import black
        print("Black is already installed.")
    except ImportError:
        print("Installing Black...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "black"])
        print("Black installed successfully.")

def setup_ruff_config():
    """Ensures Ruff is installed."""
    try:
        import ruff
        print("Ruff is already installed.")
    except ImportError:
        print("Installing Ruff...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "ruff"])
        print("Ruff installed successfully.")

def run_format():
    """Runs Black on the code directory."""
    code_dir = Path(__file__).parent.parent / "code"
    if not code_dir.exists():
        print(f"Warning: Directory {code_dir} does not exist. Skipping formatting.")
        return

    print(f"Running Black on {code_dir}...")
    try:
        subprocess.check_call([sys.executable, "-m", "black", str(code_dir)])
        print("Formatting completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error during formatting: {e}")
        # Black returns 1 if files were reformatted, which is not an error in this context
        if e.returncode != 1:
            raise

def run_lint():
    """Runs Ruff on the code directory."""
    code_dir = Path(__file__).parent.parent / "code"
    if not code_dir.exists():
        print(f"Warning: Directory {code_dir} does not exist. Skipping linting.")
        return

    print(f"Running Ruff on {code_dir}...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "check", str(code_dir)],
            capture_output=True,
            text=True
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
        
        if result.returncode == 0:
            print("Linting passed: No issues found.")
        elif result.returncode == 1:
            print("Linting found issues. Please review the output above.")
        else:
            raise subprocess.CalledProcessError(result.returncode, "ruff check")
    except subprocess.CalledProcessError as e:
        print(f"Error during linting: {e}")
        raise

def main():
    """Main entry point for setting up linting and formatting."""
    print("Setting up linting and formatting tools...")
    
    setup_black_config()
    setup_ruff_config()
    write_config_file()
    
    print("\n--- Running Formatting ---")
    run_format()
    
    print("\n--- Running Linting ---")
    try:
        run_lint()
    except subprocess.CalledProcessError:
        print("\nLinting found issues. This is expected for initial setup. Fix them manually or run 'black' and 'ruff check --fix'.")
    
    print("\nSetup complete.")

if __name__ == "__main__":
    main()