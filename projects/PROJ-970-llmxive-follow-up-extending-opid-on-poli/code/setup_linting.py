"""
Setup script for linting (Ruff) and formatting (Black) tools.
Generates configuration files required for the project's code quality standards.
"""
import os
import sys

def create_ruff_config():
    """Create .ruff.toml configuration file."""
    config_content = """[lint]
# Enable Pyflakes (`F`) and a subset of the pycodestyle (`E`)  codes by default.
select = ["E", "F", "W", "I", "N", "B", "C4", "UP", "RUF"]
ignore = ["E501", "B008"]

# Allow autofix for all enabled rules (when `--fix` is provided).
fixable = ["ALL"]
unfixable = []

# Exclude a few files.
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

# Same as Black.
line-length = 88

# Allow unused variables when underscore-prefixed.
dummy-variable-rgx = "^(_+|(_+[a-zA-Z0-9_]*[a-zA-Z0-9]+?))$"

target-version = "py311"

[lint.per-file-ignores]
"__init__.py" = ["F401"]
"""
    path = ".ruff.toml"
    with open(path, "w", encoding="utf-8") as f:
        f.write(config_content)
    print(f"Created {path}")
    return path

def create_black_config():
    """Create pyproject.toml Black configuration section if missing, or a standalone .black.toml if preferred.
    Here we append to pyproject.toml to ensure Black settings are version-controlled with the project.
    """
    config_content = """
[tool.black]
line-length = 88
target-version = ['py311']
include = '\\.pyi?$'
extend-exclude = '''
/(
    # The following are specific to Black, you probably don't want those.
    build
    | dist
    | .eggs
    | .venv
    | venv
    | __pycache__
)/
'''
"""
    # Check if pyproject.toml exists
    if os.path.exists("pyproject.toml"):
        with open("pyproject.toml", "r", encoding="utf-8") as f:
            content = f.read()
        if "[tool.black]" not in content:
            with open("pyproject.toml", "a", encoding="utf-8") as f:
                f.write(config_content)
            print("Appended Black config to pyproject.toml")
        else:
            print("Black config already exists in pyproject.toml")
    else:
        with open("pyproject.toml", "w", encoding="utf-8") as f:
            f.write(config_content)
        print("Created pyproject.toml with Black config")
    return "pyproject.toml"

def create_pre_commit_config():
    """Create .pre-commit-config.yaml for automated hooks."""
    config_content = """repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.6.9
    hooks:
- id: ruff
  args: [--fix, --exit-non-zero-on-fix]
- id: ruff-format
  - repo: https://github.com/psf/black
    rev: 24.8.0
    hooks:
- id: black
  language_version: python3.11
"""
    path = ".pre-commit-config.yaml"
    with open(path, "w", encoding="utf-8") as f:
        f.write(config_content)
    print(f"Created {path}")
    return path

def main():
    """Main entry point to setup linting and formatting."""
    print("Setting up linting (Ruff) and formatting (Black)...")
    create_ruff_config()
    create_black_config()
    create_pre_commit_config()
    print("Linting and formatting setup complete.")
    print("Run 'pip install ruff black pre-commit' to install tools.")
    print("Run 'pre-commit install' to install git hooks.")

if __name__ == "__main__":
    main()