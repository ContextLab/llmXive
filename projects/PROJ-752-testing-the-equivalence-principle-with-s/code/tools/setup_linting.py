"""
Setup script for linting (ruff) and formatting (black) tools.
Generates configuration files and installs dependencies if needed.
"""
import os
import subprocess
import sys
from pathlib import Path

def ensure_dependency(package: str, import_name: str = None):
    """Ensure a package is installed, installing it if necessary."""
    import_name = import_name or package
    try:
        __import__(import_name)
    except ImportError:
        print(f"Installing {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package, "-q"])

def write_ruff_config():
    """Write pyproject.toml with ruff configuration."""
    root = Path(__file__).resolve().parent.parent.parent
    pyproject = root / "pyproject.toml"
    
    config_content = """[tool.black]
line-length = 88
target-version = ['py311']
include = '\\.pyi?$'
extend-exclude = '''
/(
  # Directories to exclude
  \\.git
  | \\.hg
  | \\.mypy_cache
  | \\.tox
  | \\.venv
  | _build
  | buck-out
  | build
  | dist
  | data
  | figures
  | docs
)/
'''

[tool.ruff]
target-version = "py311"
line-length = 88
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

[tool.ruff.isort]
known-first-party = ["code"]
known-third-party = ["astropy", "numpy", "pandas", "pytest", "requests", "yaml"]
section-order = ["future", "standard-library", "third-party", "first-party", "local-folder"]

[tool.ruff.per-file-ignores]
"__init__.py" = ["F401"]
"code/tests/*" = ["S101"] # Allow asserts in tests
"""
    
    if pyproject.exists():
        # Append if not present, or update if present
        content = pyproject.read_text()
        if "[tool.black]" not in content:
            content += "\n" + config_content
            pyproject.write_text(content)
            print("Updated pyproject.toml with linting config.")
        else:
            print("pyproject.toml already contains linting config.")
    else:
        pyproject.write_text(config_content)
        print("Created pyproject.toml with linting config.")

def main():
    print("Setting up linting (ruff) and formatting (black)...")
    
    # Ensure dependencies
    ensure_dependency("ruff")
    ensure_dependency("black")
    
    # Write config
    write_ruff_config()
    
    print("Linting and formatting setup complete.")
    print("Run 'ruff check code/' to lint.")
    print("Run 'black code/' to format.")

if __name__ == "__main__":
    main()