import os
import sys
from pathlib import Path
from typing import List


def create_linting_config() -> None:
    """Create ruff configuration file."""
    config_content = """[tool.ruff]
# Same as Black.
line-length = 88
indent-width = 4
target-version = "py311"

[tool.ruff.lint]
# Enable Pyflakes (`F`) and a subset of the pycodestyle (`E`)  codes by default.
select = ["E4", "E7", "E9", "F", "I", "W"]
ignore = []

# Allow fix for all enabled rules (when `--fix` is provided).
fixable = ["ALL"]
unfixable = []

# Allow unused variables when underscore-prefixed.
dummy-variable-rgx = "^(_+|(_+[a-zA-Z0-9_]*[a-zA-Z0-9]+?))$"

[tool.ruff.format]
# Like Black, use double quotes for strings.
quote-style = "double"

# Like Black, indent with spaces, rather than tabs.
indent-style = "space"

# Like Black, respect magic trailing commas.
skip-magic-trailing-comma = false

# Like Black, automatically detect the appropriate line ending.
line-ending = "auto"
"""
    with open("ruff.toml", "w") as f:
        f.write(config_content)
    print("Created ruff.toml")


def create_formatting_config() -> None:
    """Create black configuration file."""
    config_content = """[tool.black]
line-length = 88
target-version = ['py311']
"""
    with open("pyproject.toml", "a") as f:
        f.write("\n")
        f.write(config_content)
    print("Updated pyproject.toml with black config")


def create_ruffignore() -> None:
    """Create .ruffignore file."""
    with open(".ruffignore", "w") as f:
        f.write("__pycache__/\n")
        f.write("*.pyc\n")
        f.write(".git/\n")
    print("Created .ruffignore")


def create_gitignore_update() -> None:
    """Update .gitignore if it exists."""
    gitignore_path = ".gitignore"
    entries = [
        "data/raw/",
        "data/processed/",
        "data/results/",
        "*.pyc",
        "__pycache__/",
    ]

    if os.path.exists(gitignore_path):
        with open(gitignore_path, "r") as f:
            content = f.read()

        for entry in entries:
            if entry not in content:
                with open(gitignore_path, "a") as f:
                    f.write(f"\n{entry}\n")
        print("Updated .gitignore")
    else:
        with open(gitignore_path, "w") as f:
            for entry in entries:
                f.write(f"{entry}\n")
        print("Created .gitignore")


def main() -> None:
    """Main entry point for linting setup."""
    create_linting_config()
    create_formatting_config()
    create_ruffignore()
    create_gitignore_update()
    print("Linting and formatting tools configured.")


if __name__ == "__main__":
    main()
