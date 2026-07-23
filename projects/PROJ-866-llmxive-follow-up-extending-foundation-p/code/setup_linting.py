import os
import sys
from pathlib import Path
from typing import List

def create_linting_config() -> Path:
    """Create ruff configuration file."""
    root = Path(__file__).parent.parent
    config_path = root / ".ruff.toml"
    
    content = """[lint]
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # pyflakes
    "I",  # isort
    "B",  # flake8-bugbear
    "C4", # flake8-comprehensions
    "UP", # pyupgrade
]
ignore = [
    "E501", # line too long (handled by black)
    "B008", # do not perform function calls in argument defaults
]

[lint.isort]
known-first-party = ["code"]
force-single-line = true

[format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "auto"
"""
    config_path.write_text(content)
    return config_path

def create_formatting_config() -> Path:
    """Create black configuration in pyproject.toml."""
    root = Path(__file__).parent.parent
    pyproject_path = root / "pyproject.toml"
    
    # Check if file exists and has content
    if pyproject_path.exists():
        content = pyproject_path.read_text()
        if "[tool.black]" in content:
            # Update existing config
            lines = content.split("\n")
            new_lines = []
            in_black_section = False
            for line in lines:
                if line.strip().startswith("[tool.black]"):
                    in_black_section = True
                    new_lines.append(line)
                    # Add or update black config
                    new_lines.append('line-length = 88')
                    new_lines.append('target-version = ["py39"]')
                    new_lines.append('')
                    continue
                if in_black_section and line.strip().startswith("["):
                    in_black_section = False
                if not in_black_section:
                    new_lines.append(line)
            pyproject_path.write_text("\n".join(new_lines))
        else:
            # Append black config
            pyproject_path.write_text(content + "\n[tool.black]\nline-length = 88\ntarget-version = [\"py39\"]\n")
    else:
        content = """[build-system]
requires = ["setuptools>=42", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "llmxive-research"
version = "0.1.0"
requires-python = ">=3.9"

[tool.black]
line-length = 88
target-version = ["py39"]
"""
        pyproject_path.write_text(content)
    
    return pyproject_path

def create_ruffignore() -> Path:
    """Create .ruffignore file."""
    root = Path(__file__).parent.parent
    ignore_path = root / ".ruffignore"
    
    content = """__pycache__
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.venv/
*/migrations/*
*/static/CACHE/*
*/node_modules/*
.pytest_cache/
.coverage
htmlcov/
"""
    ignore_path.write_text(content)
    return ignore_path

def create_gitignore_update() -> Path:
    """Update .gitignore to include linting artifacts."""
    root = Path(__file__).parent.parent
    gitignore_path = root / ".gitignore"
    
    linting_entries = """
# Linting and formatting
.ruff_cache/
__pycache__/
*.py[cod]
*$py.class
"""
    
    if gitignore_path.exists():
        content = gitignore_path.read_text()
        if ".ruff_cache/" not in content:
            gitignore_path.write_text(content + linting_entries)
    else:
        gitignore_path.write_text(linting_entries)
    
    return gitignore_path

def main():
    """Main entry point for linting setup."""
    print("Setting up linting and formatting tools...")
    
    ruff_config = create_linting_config()
    print(f"Created ruff config: {ruff_config}")
    
    pyproject = create_formatting_config()
    print(f"Updated pyproject.toml: {pyproject}")
    
    ruffignore = create_ruffignore()
    print(f"Created .ruffignore: {ruffignore}")
    
    gitignore = create_gitignore_update()
    print(f"Updated .gitignore: {gitignore}")
    
    print("Linting and formatting setup complete!")
    print("\nTo run ruff:")
    print("  ruff check .")
    print("\nTo run black:")
    print("  black .")
    print("\nTo run both:")
    print("  ruff check . && black .")

if __name__ == "__main__":
    main()