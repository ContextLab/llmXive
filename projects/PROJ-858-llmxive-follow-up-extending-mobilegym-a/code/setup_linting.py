"""
Task T003: Configure linting (ruff) and formatting (black) tools.

This script initializes the project's linting and formatting configuration,
updates requirements.txt with the necessary tools, and sets up pre-commit hooks.
"""
import os
import sys
import subprocess
import json

# Ensure the path includes the project root for imports if needed, though this script is standalone
# relative to code/.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REQUIREMENTS_PATH = os.path.join(PROJECT_ROOT, "requirements.txt")
PYPROJECT_PATH = os.path.join(PROJECT_ROOT, "pyproject.toml")
PRE_COMMIT_PATH = os.path.join(PROJECT_ROOT, ".pre-commit-config.yaml")
RUFF_TOML_PATH = os.path.join(PROJECT_ROOT, "ruff.toml") # Fallback if pyproject not used, but we prefer pyproject
BLACK_TOML_PATH = os.path.join(PROJECT_ROOT, "black.toml") # Fallback

def ensure_tool_in_requirements(tool_name: str, version: str) -> None:
    """Ensures a tool and version are present in requirements.txt."""
    if not os.path.exists(REQUIREMENTS_PATH):
        with open(REQUIREMENTS_PATH, "w") as f:
            f.write(f"{tool_name}=={version}\n")
        return

    with open(REQUIREMENTS_PATH, "r") as f:
        lines = f.readlines()

    updated = False
    new_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(tool_name):
            # Update existing line
            new_lines.append(f"{tool_name}=={version}\n")
            updated = True
        else:
            new_lines.append(line)

    if not updated:
        new_lines.append(f"{tool_name}=={version}\n")

    with open(REQUIREMENTS_PATH, "w") as f:
        f.writelines(new_lines)
    
    print(f"Updated requirements.txt: {tool_name}=={version}")

def create_ruff_config() -> None:
    """Creates a ruff.toml configuration file."""
    # We will use pyproject.toml for ruff config to keep it standard, 
    # but if the project prefers a separate file, we can do that. 
    # The prompt asks to configure ruff. Standard practice is pyproject.toml.
    # Let's create/update pyproject.toml.
    
    config_content = """
[tool.ruff]
# Enable pycodestyle (`E`) and Pyflakes (`F`) codes by default.
select = ["E", "F", "W", "I", "N", "UP", "B", "C4", "ARG", "SIM"]
ignore = []

# Allow autofix for all enabled rules (when `--fix` is provided).
fixable = ["ALL"]
unfixable = []

# A list of file patterns to exclude from analysis.
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
    "data/raw",
    "data/processed",
    "data/validation",
]

# Same as Black.
line-length = 88

# Allow unused variables when underscore-prefixed.
dummy-variable-rgx = "^(_+|(_+[a-zA-Z0-9_]*[a-zA-Z0-9]+?))$"

# Target version
target-version = "py310"

[tool.ruff.per-file-ignores]
"__init__.py" = ["F401"]

[tool.ruff.format]
# Use double quotes for strings.
quote-style = "double"

# Indent with spaces, rather than tabs.
indent-style = "space"

# Respect magic trailing commas.
skip-magic-trailing-comma = false

# Automatically detect the preferred line ending.
line-ending = "auto"
"""
    
    with open(PYPROJECT_PATH, "r") as f:
        existing_content = f.read()
    
    # Simple check to see if [tool.ruff] exists
    if "[tool.ruff]" in existing_content:
        print(f"Updating existing {PYPROJECT_PATH} with ruff config...")
        # In a real scenario, we might parse and merge, but for this task,
        # we will overwrite the relevant section or append if missing.
        # To be safe and idempotent for a script, we'll just append if not found,
        # or replace the block. Let's just write the full config if it's simple.
        # Actually, to avoid breaking other tool configs, we should be careful.
        # For this task, let's assume we can append or we create a dedicated ruff.toml 
        # if we want to be 100% safe from conflicting with other tools in pyproject.
        # However, the standard is pyproject. Let's try to insert.
        
        # Simpler approach for this task: Create a dedicated ruff.toml if pyproject is complex?
        # No, let's stick to the prompt's implied need: "Configure ruff".
        # I will write a dedicated ruff.toml to avoid merging logic complexity and ensure it's there.
        # The API surface doesn't show pyproject handling, so a separate file is safer.
        pass

    # Let's use a dedicated ruff.toml to avoid parsing pyproject.toml which might have other tools
    ruff_config = """
[lint]
select = ["E", "F", "W", "I", "N", "UP", "B", "C4", "ARG", "SIM"]
ignore = []
fixable = ["ALL"]
unfixable = []
exclude = [
    ".bzr", ".direnv", ".eggs", ".git", ".git-rewrite", ".hg", ".mypy_cache",
    ".nox", ".pants.d", ".pytype", ".ruff_cache", ".svn", ".tox", ".venv",
    "__pypackages__", "_build", "buck-out", "build", "dist", "node_modules", "venv",
    "data/raw", "data/processed", "data/validation"
]
line-length = 88
dummy-variable-rgx = "^(_+|(_+[a-zA-Z0-9_]*[a-zA-Z0-9]+?))$"
target-version = "py310"

[lint.per-file-ignores]
"__init__.py" = ["F401"]

[format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "auto"
"""
    with open(RUFF_TOML_PATH, "w") as f:
        f.write(ruff_config)
    print(f"Created {RUFF_TOML_PATH}")

def create_black_config() -> None:
    """Creates a black configuration in pyproject.toml."""
    config_content = """
[tool.black]
line-length = 88
target-version = ['py310']
include = '\\.pyi?$'
exclude = '''
/(
    \.bzr
    | \.direnv
    | \.eggs
    | \.git
    | \.git-rewrite
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
    | data/raw
    | data/processed
    | data/validation
)/
'''
"""
    
    # We append to pyproject.toml to avoid overwriting other tools
    if os.path.exists(PYPROJECT_PATH):
        with open(PYPROJECT_PATH, "r") as f:
            content = f.read()
        
        if "[tool.black]" in content:
            print(f"{PYPROJECT_PATH} already has black config.")
            return
        
        with open(PYPROJECT_PATH, "a") as f:
            f.write("\n" + config_content)
    else:
        with open(PYPROJECT_PATH, "w") as f:
            f.write(config_content)
    
    print(f"Updated {PYPROJECT_PATH} with black config.")

def create_pre_commit_config() -> None:
    """Creates a .pre-commit-config.yaml file."""
    config_content = """
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
- id: trailing-whitespace
- id: end-of-file-fixer
- id: check-yaml
- id: check-added-large-files

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.6
    hooks:
- id: ruff
  args: [--fix, --exit-non-zero-on-fix]
- id: ruff-format

  - repo: https://github.com/psf/black-pre-commit-mirror
    rev: 23.11.0
    hooks:
- id: black
"""
    with open(PRE_COMMIT_PATH, "w") as f:
        f.write(config_content)
    print(f"Created {PRE_COMMIT_PATH}")

def main():
    """Main entry point for T003."""
    print("Starting T003: Configure linting (ruff) and formatting (black)...")
    
    # 1. Add tools to requirements.txt
    ensure_tool_in_requirements("ruff", "0.1.6")
    ensure_tool_in_requirements("black", "23.11.0")
    ensure_tool_in_requirements("pre-commit", "3.5.0")
    
    # 2. Create configuration files
    create_ruff_config()
    create_black_config()
    create_pre_commit_config()
    
    print("T003 completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())