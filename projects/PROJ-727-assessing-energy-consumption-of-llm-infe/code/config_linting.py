"""
Configuration module for linting (Ruff) and formatting (Black) tools.
Generates necessary configuration files and updates requirements.
"""
import os
import sys
from pathlib import Path
import toml

# Project root relative to this file
PROJECT_ROOT = Path(__file__).resolve().parent.parent

def write_ruff_config():
    """Create .ruff.toml with project-specific linting rules."""
    ruff_config_path = PROJECT_ROOT / ".ruff.toml"
    
    config_content = """[lint]
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
    "E501", # Line too long (handled by Black)
    "B008", # Do not perform function call in argument defaults (common in FastAPI/pytest)
]

[lint.per-file-ignores]
"__init__.py" = ["F401"] # Ignore unused imports in init files

[format]
# Use Black-compatible settings
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "auto"
"""
    
    with open(ruff_config_path, "w", encoding="utf-8") as f:
        f.write(config_content)
    
    print(f"Created Ruff config: {ruff_config_path}")
    return ruff_config_path

def write_black_config():
    """Create pyproject.toml section for Black formatting if not exists, or update it."""
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    
    # Read existing content if file exists
    if pyproject_path.exists():
        with open(pyproject_path, "r", encoding="utf-8") as f:
            content = f.read()
        try:
            config = toml.loads(content)
        except toml.TomlDecodeError:
            config = {}
    else:
        config = {}
    
    # Ensure [tool.black] section exists
    if "tool" not in config:
        config["tool"] = {}
    
    config["tool"]["black"] = {
        "line-length": 88,
        "target-version": ['py310'],
        "skip-string-normalization": False,
        "exclude": r'/(\.git|\.venv|venv|__pycache__|build|dist)/'
    }
    
    # Write back
    with open(pyproject_path, "w", encoding="utf-8") as f:
        toml.dump(config, f)
    
    print(f"Updated Black config in: {pyproject_path}")
    return pyproject_path

def write_pre_commit_config():
    """Create .pre-commit-config.yaml to hook Ruff and Black."""
    pre_commit_path = PROJECT_ROOT / ".pre-commit-config.yaml"
    
    config_content = """repos:
  - repo: https://github.com/psf/black
    rev: 24.4.2
    hooks:
- id: black
  language_version: python3.10
  
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.4.8
    hooks:
- id: ruff
  args: [--fix, --exit-non-zero-on-fix]
- id: ruff-format
"""
    
    with open(pre_commit_path, "w", encoding="utf-8") as f:
        f.write(config_content)
    
    print(f"Created Pre-commit config: {pre_commit_path}")
    return pre_commit_path

def update_requirements():
    """Ensure requirements.txt includes dev dependencies for linting."""
    requirements_path = PROJECT_ROOT / "requirements.txt"
    
    dev_deps = [
        "ruff>=0.4.0",
        "black>=24.4.0",
        "pre-commit>=3.7.0",
        "toml>=0.10.2"
    ]
    
    existing_deps = []
    if requirements_path.exists():
        with open(requirements_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    # Normalize package name for comparison
                    pkg_name = line.lower().split("==")[0].split(">=")[0].split("<=")[0].split(">")[0].split("<")[0].strip()
                    existing_deps.append(pkg_name)
    
    # Check what needs to be added
    to_add = []
    for dep in dev_deps:
        pkg_name = dep.lower().split("==")[0].split(">=")[0].split("<=")[0].split(">")[0].split("<")[0].strip()
        if pkg_name not in existing_deps:
            to_add.append(dep)
    
    if to_add:
        with open(requirements_path, "a", encoding="utf-8") as f:
            f.write("\n# Development dependencies\n")
            for dep in to_add:
                f.write(dep + "\n")
        print(f"Added dev dependencies to requirements.txt: {to_add}")
    else:
        print("All dev dependencies already present in requirements.txt")
    
    return requirements_path

def main():
    """Main entry point to configure linting and formatting tools."""
    print("Configuring linting and formatting tools...")
    
    try:
        write_ruff_config()
        write_black_config()
        write_pre_commit_config()
        update_requirements()
        
        print("\nConfiguration complete. To use:")
        print("  1. Install dependencies: pip install -r requirements.txt")
        print("  2. Initialize pre-commit: pre-commit install")
        print("  3. Run linter: ruff check .")
        print("  4. Run formatter: black .")
        print("  5. Run all hooks: pre-commit run --all-files")
        
        return 0
    except Exception as e:
        print(f"Error during configuration: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())