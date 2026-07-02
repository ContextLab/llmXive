import os
import sys
from pathlib import Path

def ensure_dir(path: Path) -> None:
    """Ensure the directory exists."""
    path.mkdir(parents=True, exist_ok=True)

def write_ruff_config(root: Path) -> None:
    """Write ruff.toml configuration file."""
    config_path = root / "ruff.toml"
    content = """# Ruff configuration for llmXive project

# Target Python version
target-version = "py311"

# Line length
line-length = 88

[lint]
# Enable pycodestyle (`E`), Pyflakes (`F`), and isort (`I`)
select = ["E", "F", "I", "W", "N", "D"]

# Ignore specific rules if needed
ignore = [
    "D100",  # Missing docstring in public module
    "D104",  # Missing docstring in public package
    "D203",  # 1 blank line required before class docstring (conflicts with D211)
    "D213",  # Multi-line docstring summary should start at the second line (conflicts with D212)
]

# Allow autofix for all enabled rules
fixable = ["ALL"]
unfixable = []

[lint.per-file-ignores]
"__init__.py" = ["F401"]  # Ignore unused imports in __init__.py

[lint.isort]
known-first-party = ["utils", "tests", "tools"]

[format]
# Use double quotes for strings
quote-style = "double"

# Indent with spaces
indent-style = "space"

# Skip magic trailing comma
skip-magic-trailing-comma = false

# Line length
line-length = 88
"""
    config_path.write_text(content)
    print(f"Created {config_path}")

def write_black_config(root: Path) -> None:
    """Write pyproject.toml with Black configuration."""
    config_path = root / "pyproject.toml"
    
    # Check if file exists and has content
    existing_content = ""
    if config_path.exists():
        existing_content = config_path.read_text()
    
    # Basic pyproject.toml content with Black config
    # We append to existing content if it exists, or create new
    black_section = """
[tool.black]
line-length = 88
target-version = ['py311']
include = '\\.pyi?$'
extend-exclude = '''
/(
  # directories
  \\.eggs
  | \\.git
  | \\.hg
  | \\.mypy_cache
  | \\.tox
  | \\.venv
  | build
  | dist
)/
'''

[tool.ruff]
# This section is managed by ruff.toml, but we keep this for compatibility
"""

    if not existing_content.strip():
        final_content = f"[project]\nname = \"llmXive-proj-036\"\nversion = \"0.1.0\"\n{black_section}"
    else:
        # Simple append if pyproject.toml exists but doesn't have tool sections
        if "[tool.black]" not in existing_content:
            final_content = existing_content + black_section
        else:
            final_content = existing_content
    
    config_path.write_text(final_content)
    print(f"Updated {config_path} with Black configuration")

def update_requirements(root: Path) -> None:
    """Ensure ruff and black are in requirements.txt."""
    req_path = root / "requirements.txt"
    
    if not req_path.exists():
        print("requirements.txt not found. Creating with linting tools.")
        req_path.write_text("numpy\nscipy\nastropy\nhealpy\ncamb\nnbodykit\nfitsio\nrequests\npytest\n")
    
    content = req_path.read_text()
    
    linting_deps = ["ruff", "black"]
    updated = False
    
    for dep in linting_deps:
        if dep not in content:
            content += f"{dep}\n"
            updated = True
            print(f"Added {dep} to requirements.txt")
    
    if updated:
        req_path.write_text(content)
    else:
        print("Linting tools already present in requirements.txt")

def main() -> None:
    """Main entry point to configure linting and formatting."""
    # Determine project root (assume script is in code/tools/)
    script_path = Path(__file__).resolve()
    root = script_path.parent.parent.parent
    
    print(f"Configuring linting and formatting for project at: {root}")
    
    # Create ruff config
    write_ruff_config(root)
    
    # Create/update pyproject.toml with Black config
    write_black_config(root)
    
    # Update requirements.txt
    update_requirements(root)
    
    print("\nLinting and formatting configuration complete!")
    print("\nNext steps:")
    print("1. Install tools: pip install -r requirements.txt")
    print("2. Run formatter: black code/")
    print("3. Run linter: ruff check code/")

if __name__ == "__main__":
    main()