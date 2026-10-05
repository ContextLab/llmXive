import os
import subprocess
import sys
from pathlib import Path

def write_config_file(config_path: Path, content: str) -> None:
    """Write configuration content to a file."""
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w", encoding="utf-8") as f:
        f.write(content)

def setup_black_config() -> Path:
    """Create or update pyproject.toml with Black configuration."""
    pyproject_path = Path("pyproject.toml")
    
    if pyproject_path.exists():
        content = pyproject_path.read_text(encoding="utf-8")
        if "[tool.black]" in content:
            return pyproject_path
    else:
        content = ""

    black_config = """
[tool.black]
line-length = 88
target-version = ['py38', 'py39', 'py310', 'py311']
include = '\\.pyi?$'
exclude = '''
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
'''
"""
    if "[tool.black]" not in content:
        content += black_config
        pyproject_path.write_text(content, encoding="utf-8")
    
    return pyproject_path

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
target-version = "py38"
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # Pyflakes
    "I",  # isort
    "B",  # flake8-bugbear
    "C4", # flake8-comprehensions
    "UP", # pyupgrade
]
ignore = [
    "E501", # line too long (handled by black)
    "B008", # do not perform function calls in argument defaults
    "C901", # too complex
]

[tool.ruff.per-file-ignores]
"__init__.py" = ["F401"]

[tool.ruff.isort]
known-first-party = ["codecarbon", "datasets", "transformers", "pandas", "matplotlib", "seaborn", "scikit-learn"]
"""
    if "[tool.ruff]" not in content:
        content += ruff_config
        pyproject_path.write_text(content, encoding="utf-8")
    
    return pyproject_path

def run_format() -> int:
    """Run Black formatter on the codebase."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "black", "code/", "tests/"],
            check=False,
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print(f"Black formatting output:\n{result.stdout}")
            print(f"Black formatting errors:\n{result.stderr}")
        return result.returncode
    except FileNotFoundError:
        print("Error: Black is not installed. Run: pip install black")
        return 1

def run_lint() -> int:
    """Run Ruff linter on the codebase."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "check", "code/", "tests/"],
            check=False,
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print(f"Ruff linting output:\n{result.stdout}")
            print(f"Ruff linting errors:\n{result.stderr}")
        return result.returncode
    except FileNotFoundError:
        print("Error: Ruff is not installed. Run: pip install ruff")
        return 1

def main() -> int:
    """Main entry point for setting up linting and formatting tools."""
    print("Setting up linting (Ruff) and formatting (Black)...")
    
    # Create config files
    pyproject_path = setup_black_config()
    print(f"Black configuration written to: {pyproject_path}")
    
    setup_ruff_config()
    print(f"Ruff configuration written to: {pyproject_path}")
    
    # Check if tools are installed
    try:
        subprocess.run([sys.executable, "-m", "black", "--version"], check=True, capture_output=True)
        print("Black is installed.")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Warning: Black is not installed. Install with: pip install black")
    
    try:
        subprocess.run([sys.executable, "-m", "ruff", "--version"], check=True, capture_output=True)
        print("Ruff is installed.")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Warning: Ruff is not installed. Install with: pip install ruff")
    
    print("\nConfiguration complete. To format code, run: black code/ tests/")
    print("To lint code, run: ruff check code/ tests/")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())