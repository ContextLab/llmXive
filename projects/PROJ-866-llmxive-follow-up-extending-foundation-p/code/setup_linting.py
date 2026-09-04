import os
import sys
from pathlib import Path
from typing import List

def create_linting_config() -> str:
    """Create ruff configuration file."""
    return """[tool.ruff]
# Enable pycodestyle (`E`) and Pyflakes (`F`) codes by default.
select = ["E", "F", "W", "I", "N", "UP", "B", "C4", "ARG", "SIM"]
ignore = ["E501", "W505"]

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

target-version = "py310"

[tool.ruff.per-file-ignores]
"__init__.py" = ["F401"]
"""

def create_formatting_config() -> str:
    """Create black configuration in pyproject.toml."""
    return """[tool.black]
line-length = 88
target-version = ['py310']
include = '\\.pyi?$'
exclude = '''
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

def create_ruffignore() -> str:
    """Create .ruffignore file."""
    return """# Ignore ruff in these directories
__pycache__
.venv
venv
.git
"""

def create_gitignore_update() -> str:
    """Create gitignore update for linting artifacts."""
    return """# Linting and Formatting
.ruff_cache/
.black_cache/
.mypy_cache/
"""

def main() -> None:
    """Main entry point to configure linting and formatting."""
    root = Path(".")
    
    # Create pyproject.toml if it doesn't exist, or append to it
    pyproject_path = root / "pyproject.toml"
    
    # Read existing content if present
    existing_content = ""
    if pyproject_path.exists():
        existing_content = pyproject_path.read_text()
    
    # Check if [tool.black] section already exists
    if "[tool.black]" not in existing_content:
        black_config = create_formatting_config()
        if existing_content and not existing_content.endswith("\n"):
            existing_content += "\n\n"
        existing_content += black_config
        pyproject_path.write_text(existing_content)
        print(f"Added Black configuration to {pyproject_path}")
    else:
        print(f"Black configuration already exists in {pyproject_path}")
    
    # Create .ruff.toml
    ruff_config_path = root / "ruff.toml"
    ruff_content = create_linting_config()
    ruff_config_path.write_text(ruff_content)
    print(f"Created {ruff_config_path}")
    
    # Create .ruffignore
    ruffignore_path = root / ".ruffignore"
    ruffignore_content = create_ruffignore()
    ruffignore_path.write_text(ruffignore_content)
    print(f"Created {ruffignore_path}")
    
    # Update .gitignore
    gitignore_path = root / ".gitignore"
    gitignore_update = create_gitignore_update()
    
    if gitignore_path.exists():
        gitignore_content = gitignore_path.read_text()
        if "ruff_cache" not in gitignore_content:
            if not gitignore_content.endswith("\n"):
                gitignore_content += "\n"
            gitignore_content += gitignore_update
            gitignore_path.write_text(gitignore_content)
            print(f"Updated {gitignore_path}")
        else:
            print(f"Gitignore already contains ruff entries")
    else:
        gitignore_path.write_text(gitignore_update)
        print(f"Created {gitignore_path}")
    
    print("\nLinting and formatting configuration complete.")
    print("To format code: black code/")
    print("To lint code: ruff check code/")

if __name__ == "__main__":
    main()
