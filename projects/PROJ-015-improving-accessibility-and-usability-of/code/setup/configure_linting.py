"""
Configuration script for linting (ruff) and formatting (black) tools.
This script ensures the necessary configuration files exist and dependencies are installed.
"""
import os
import sys
import subprocess
import importlib.metadata
from pathlib import Path

def get_project_root() -> Path:
    """Determine the project root directory."""
    current = Path(__file__).resolve()
    # Traverse up to find the root (usually where code/ is a direct subdir)
    while current != current.parent:
        if (current / "code").is_dir() and (current / "data").is_dir():
            return current
        current = current.parent
    # Fallback: assume current working directory if structure not found
    return Path.cwd()

def ensure_package(package_name: str) -> bool:
    """
    Check if a package is installed. If not, attempt to install it.
    Returns True if the package is available after the check.
    """
    try:
        importlib.metadata.version(package_name)
        return True
    except importlib.metadata.PackageNotFoundError:
        print(f"Installing {package_name}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
            return True
        except subprocess.CalledProcessError:
            print(f"Failed to install {package_name}. Please install manually.")
            return False

def write_file_if_missing(filepath: Path, content: str) -> None:
    """Write content to a file only if it doesn't exist or is empty."""
    if filepath.exists():
        with open(filepath, "r", encoding="utf-8") as f:
            if f.read().strip():
                print(f"Configuration file {filepath} already exists and is not empty. Skipping.")
                return
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Created/Updated configuration file: {filepath}")

def main() -> int:
    """Main entry point for configuring linting and formatting tools."""
    root = get_project_root()
    print(f"Project root detected at: {root}")

    # 1. Ensure dependencies are installed
    packages = ["ruff", "black"]
    for pkg in packages:
        if not ensure_package(pkg):
            print(f"Error: Could not ensure {pkg} is installed. Aborting.")
            return 1

    # 2. Create ruff configuration (.ruff.toml)
    ruff_config_path = root / ".ruff.toml"
    ruff_content = """
# Ruff configuration
target-version = "py311"

[lint]
# Enable pycodestyle (`E`) and Pyflakes (`F`) codes by default.
select = ["E", "F", "I", "N", "W", "UP", "C90"]
ignore = []

# Allow autofix for all enabled rules (when `--fix` is provided).
fixable = ["ALL"]
unfixable = []

# Exclude a few problematic directories/files if necessary
exclude = [
    ".bzr",
    ".direnv",
    ".eggs",
    ".git",
    ".git-rewrite",
    ".hg",
    ".mypy_cache",
    ".nox",
    ".pants.d",
    ".pytype",
    ".ruff_cache",
    ".svn",
    ".tox",
    ".venv",
    "__pypackages__",
    "_build",
    "buck-out",
    "build",
    "dist",
    "node_modules",
    "venv",
]

[lint.per-file-ignores]
# Ignore specific rules for specific files if needed
"__init__.py" = ["F401"]

[format]
# Use spaces for indentation.
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "auto"
"""
    write_file_if_missing(ruff_config_path, ruff_content)

    # 3. Create Black configuration (pyproject.toml)
    # We append to pyproject.toml if it exists, or create a new one if not.
    pyproject_path = root / "pyproject.toml"
    
    black_section = """
[tool.black]
line-length = 88
target-version = ['py311']
include = '\\.pyi?$'
extend-exclude = '''
/(
    \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.nox
  | \.pants.d
  | \.pytype
  | \.ruff_cache
  | \.svn
  | \.tox
  | \.venv
  | __pypackages__
  | _build
  | buck-out
  | build
  | dist
  | node_modules
  | venv
)/
'''
"""
    
    if pyproject_path.exists():
        with open(pyproject_path, "r", encoding="utf-8") as f:
            existing_content = f.read()
        
        # Check if [tool.black] already exists
        if "[tool.black]" not in existing_content:
            with open(pyproject_path, "a", encoding="utf-8") as f:
                f.write("\n" + black_section)
            print("Appended Black configuration to pyproject.toml")
        else:
            print("[tool.black] section already exists in pyproject.toml. Skipping.")
    else:
        with open(pyproject_path, "w", encoding="utf-8") as f:
            f.write("[project]\nname = \"llmxive-project\"\nversion = \"0.1.0\"\n\n" + black_section)
        print("Created new pyproject.toml with Black configuration")

    # 4. Create .gitignore entries for linting artifacts if missing
    gitignore_path = root / ".gitignore"
    linting_entries = [
        "\n# Python linting and formatting artifacts\n.ruff_cache/",
        "__pycache__/",
        "*.py[cod]",
        "*$py.class",
        ".mypy_cache/",
        ".pytest_cache/",
        ".coverage",
        "htmlcov/",
    ]
    
    needs_update = False
    if gitignore_path.exists():
        with open(gitignore_path, "r", encoding="utf-8") as f:
            content = f.read()
            for entry in linting_entries:
                if entry.strip() not in content:
                    needs_update = True
                    break
    
    if needs_update or not gitignore_path.exists():
        with open(gitignore_path, "a", encoding="utf-8") as f:
            f.write("\n# Linting and Formatting\n.ruff_cache/\n")
        print("Updated .gitignore with linting artifacts")

    print("Linting and formatting tools configured successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())