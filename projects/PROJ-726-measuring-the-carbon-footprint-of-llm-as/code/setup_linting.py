import os
import subprocess
import sys
from pathlib import Path

def write_config_file(path: Path, content: str) -> None:
    """Write configuration content to a file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def setup_black_config(project_root: Path) -> Path:
    """Create pyproject.toml with Black configuration if it doesn't exist or update it."""
    pyproject_path = project_root / "pyproject.toml"
    
    black_config = """
[tool.black]
line-length = 88
target-version = ['py311']
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
    
    if pyproject_path.exists():
        with open(pyproject_path, "r", encoding="utf-8") as f:
            content = f.read()
            if "[tool.black]" not in content:
                content += black_config
                with open(pyproject_path, "w", encoding="utf-8") as f:
                    f.write(content)
    else:
        write_config_file(pyproject_path, black_config)
    
    return pyproject_path

def setup_ruff_config(project_root: Path) -> Path:
    """Create .ruff.toml with Ruff configuration."""
    ruff_config_path = project_root / ".ruff.toml"
    
    ruff_config = """
# Exclude a few common directories
exclude = [
    ".git",
    ".hg",
    ".mypy_cache",
    ".tox",
    ".venv",
    "_build",
    "buck-out",
    "build",
    "dist",
]

# Same as Black
line-length = 88

# Assume Python 3.11
target-version = "py311"

[lint]
# Enable pycodestyle (`E`) and Pyflakes (`F`) codes by default.
select = ["E", "F", "W", "I", "N", "UP", "B", "C4", "SIM"]
ignore = []

# Allow autofix for all enabled rules (when `--fix` is provided).
fixable = ["ALL"]
unfixable = []

# Allow unused variables when underscore-prefixed.
dummy-variable-rgx = "^(_+|(_+[a-zA-Z0-9_]*[a-zA-Z0-9]+?))$"

[lint.per-file-ignores]
# Ignore specific rules for specific files if needed
"__init__.py" = ["F401"]

[lint.isort]
force-single-line = false
lines-after-imports = 2
known-first-party = []
known-third-party = []

[lint.pydocstyle]
convention = "google"
"""
    
    write_config_file(ruff_config_path, ruff_config)
    return ruff_config_path

def run_format(project_root: Path) -> None:
    """Run Black formatter on the project."""
    try:
        subprocess.run(
            [sys.executable, "-m", "black", "code/", "tests/"],
            cwd=project_root,
            check=True,
            capture_output=False
        )
    except subprocess.CalledProcessError as e:
        print(f"Error running Black formatter: {e}")
        raise

def run_lint(project_root: Path) -> None:
    """Run Ruff linter on the project."""
    try:
        subprocess.run(
            [sys.executable, "-m", "ruff", "check", "code/", "tests/"],
            cwd=project_root,
            check=True,
            capture_output=False
        )
    except subprocess.CalledProcessError as e:
        print(f"Error running Ruff linter: {e}")
        raise

def main() -> None:
    """Main entry point for setting up linting and formatting tools."""
    project_root = Path(__file__).parent.parent
    print(f"Setting up linting and formatting tools in {project_root}")
    
    # Create configuration files
    setup_black_config(project_root)
    print("Black configuration created/updated in pyproject.toml")
    
    setup_ruff_config(project_root)
    print("Ruff configuration created in .ruff.toml")
    
    # Install tools if not already installed
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-q", "black", "ruff"],
            check=True,
            capture_output=True
        )
        print("Black and Ruff installed successfully")
    except subprocess.CalledProcessError:
        print("Warning: Could not install Black and Ruff. Please install manually.")
        raise

if __name__ == "__main__":
    main()