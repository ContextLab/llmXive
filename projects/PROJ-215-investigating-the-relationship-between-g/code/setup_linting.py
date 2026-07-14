import os
import sys
from pathlib import Path

def create_black_config() -> str:
    """Return the contents of a pyproject.toml [tool.black] section."""
    return """
[tool.black]
line-length = 88
target-version = ['py38', 'py39', 'py310', 'py311']
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

def create_ruff_config() -> str:
    """Return the contents of a pyproject.toml [tool.ruff] section."""
    return """
[tool.ruff]
# Same as Black.
line-length = 88
indent-width = 4

# Assume Python 3.8+
target-version = "py38"

[tool.ruff.lint]
# Enable Pyflakes (`F`) and a subset of the pycodestyle (`E`) codes.
select = ["E4", "E7", "E9", "F", "I", "N", "W"]
ignore = []

# Allow fix for all enabled rules (when `--fix` is provided).
fixable = ["ALL"]
unfixable = []

# Exclude a few files/directories.
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

[tool.ruff.lint.per-file-ignores]
"__init__.py" = ["F401"]
"""

def update_requirements() -> str:
    """Return the linting dependencies to append to requirements.txt."""
    return """
# Linting and Formatting
ruff>=0.1.0
black>=23.0.0
"""

def create_gitignore_entries() -> str:
    """Return entries to add to .gitignore for linting artifacts."""
    return """
# Linting/Formatting caches
.ruff_cache/
.black_cache/
"""

def main() -> None:
    """
    Create configuration files for Black and Ruff.
    This script writes `pyproject.toml` (appending if it exists) to the project root.
    """
    root = Path(__file__).resolve().parent.parent
    pyproject_path = root / "pyproject.toml"

    black_section = create_black_config()
    ruff_section = create_ruff_config()

    # Check if pyproject.toml exists and has sections
    content = ""
    if pyproject_path.exists():
        content = pyproject_path.read_text()
        # Simple check to avoid duplicating sections if run multiple times
        if "[tool.black]" in content:
            print("Warning: [tool.black] section already exists in pyproject.toml. Skipping.")
            black_section = ""
        if "[tool.ruff]" in content:
            print("Warning: [tool.ruff] section already exists in pyproject.toml. Skipping.")
            ruff_section = ""

    # Combine sections
    new_content = ""
    if black_section:
        new_content += black_section.strip() + "\n\n"
    if ruff_section:
        new_content += ruff_section.strip() + "\n"

    if new_content:
        with open(pyproject_path, "a", encoding="utf-8") as f:
            f.write(new_content)
        print(f"Successfully updated {pyproject_path} with linting configurations.")
    else:
        print("No configuration changes made.")

    # Update requirements.txt
    req_path = root / "requirements.txt"
    lint_deps = update_requirements()
    if req_path.exists():
        req_content = req_path.read_text()
        # Check if already added
        if "ruff" not in req_content:
            with open(req_path, "a", encoding="utf-8") as f:
                f.write("\n" + lint_deps)
            print(f"Successfully updated {req_path} with linting dependencies.")
        else:
            print(f"Linting dependencies already present in {req_path}.")
    else:
        # Create if missing (should not happen based on T002, but safe to handle)
        with open(req_path, "w", encoding="utf-8") as f:
            f.write(lint_deps)
        print(f"Created {req_path} with linting dependencies.")

    # Update .gitignore
    gitignore_path = root / ".gitignore"
    git_entries = create_gitignore_entries()
    if gitignore_path.exists():
        git_content = gitignore_path.read_text()
        if ".ruff_cache/" not in git_content:
            with open(gitignore_path, "a", encoding="utf-8") as f:
                f.write("\n" + git_entries)
            print(f"Successfully updated {gitignore_path}.")
        else:
            print(f"Linting cache entries already present in {gitignore_path}.")
    else:
        with open(gitignore_path, "w", encoding="utf-8") as f:
            f.write(git_entries)
        print(f"Created {gitignore_path}.")

if __name__ == "__main__":
    main()