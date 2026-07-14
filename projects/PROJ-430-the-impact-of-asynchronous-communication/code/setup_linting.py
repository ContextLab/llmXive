"""
Setup script to generate configuration files for linting and formatting.
This script creates .ruff.toml and .black.toml in the code/ directory
if they do not already exist, ensuring consistent tooling across the project.
"""
import os
import sys

# Configuration content for Ruff
RUFF_CONFIG = """[lint]
# Enable pycodestyle (`E`), Pyflakes (`F`), and isort (`I`) rules
select = ["E", "F", "I", "W", "N", "UP", "B", "C4", "SIM"]
ignore = []

# Allow autofix for all enabled rules
fixable = ["ALL"]
unfixable = []

# Exclude specific files or directories
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
    "data",
    "figures",
]

# Same as `--line-length`
line-length = 100

# Allow unused variables when they start with an underscore
dummy-variable-rgx = "^(_+|(_+[a-zA-Z0-9_]*[a-zA-Z0-9]+?))$"

[lint.isort]
known-first-party = ["code", "tests"]
force-sort-within-sections = true
lines-after-imports = 2
"""

# Configuration content for Black
BLACK_CONFIG = """[tool.black]
line-length = 100
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
    | data
    | figures
)/
'''
extend-exclude = "data/|figures/"
"""

def ensure_directory_exists(path: str) -> None:
    """Ensure the directory for the given path exists."""
    directory = os.path.dirname(path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)
        print(f"Created directory: {directory}")

def write_config_file(path: str, content: str) -> None:
    """Write configuration content to a file if it doesn't exist."""
    if os.path.exists(path):
        print(f"Configuration file already exists: {path}")
        return

    ensure_directory_exists(path)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Created configuration file: {path}")

def main():
    """Main entry point for setting up linting and formatting tools."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    code_dir = os.path.join(project_root, "code")

    ruff_path = os.path.join(code_dir, ".ruff.toml")
    black_path = os.path.join(code_dir, ".black.toml")

    print("Setting up linting (ruff) and formatting (black) tools...")

    write_config_file(ruff_path, RUFF_CONFIG)
    write_config_file(black_path, BLACK_CONFIG)

    print("\nSetup complete. To verify installation, run:")
    print("  pip install -r requirements.txt")
    print("  ruff check code/")
    print("  black --check code/")

if __name__ == "__main__":
    main()
