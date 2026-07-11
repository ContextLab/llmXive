"""
Setup script to configure linting (ruff) and formatting (black) tools.
This script generates the necessary configuration files for the project.
"""
import os
import sys

def create_linting_config():
    """Create ruff.toml configuration file."""
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
    "E501", # line too long (handled by black)
    "B008", # do not perform function calls in argument defaults
]

[lint.isort]
known-first-party = ["code", "tests", "data"]
known-third-party = ["numpy", "pandas", "networkx", "tiktoken", "scipy", "statsmodels", "pytest"]

[format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "auto"
"""
    os.makedirs("code", exist_ok=True)
    with open("code/ruff.toml", "w") as f:
        f.write(config_content)
    print("Created code/ruff.toml")

def create_formatting_config():
    """Create pyproject.toml section for black configuration."""
    # Check if pyproject.toml exists
    if os.path.exists("pyproject.toml"):
        with open("pyproject.toml", "r") as f:
            content = f.read()
        
        # Check if [tool.black] section already exists
        if "[tool.black]" not in content:
            content += """
[tool.black]
line-length = 88
target-version = ['py310']
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
            with open("pyproject.toml", "w") as f:
                f.write(content)
            print("Updated pyproject.toml with black configuration")
        else:
            print("Black configuration already exists in pyproject.toml")
    else:
        # Create new pyproject.toml
        pyproject_content = """[project]
name = "llmXive"
version = "0.1.0"
description = "Automated science pipeline for agentic society coordination"
requires-python = ">=3.10"
dependencies = [
    "networkx>=3.0",
    "tiktoken>=0.5.0",
    "numpy>=1.24.0",
    "pandas>=2.0.0",
    "scipy>=1.10.0",
    "statsmodels>=0.14.0",
    "pytest>=7.0.0",
]

[project.optional-dependencies]
dev = [
    "ruff>=0.1.0",
    "black>=23.0.0",
]

[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[tool.black]
line-length = 88
target-version = ['py310']
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
        with open("pyproject.toml", "w") as f:
            f.write(pyproject_content)
        print("Created pyproject.toml with black configuration")

def create_ruffignore():
    """Create .ruffignore file."""
    ignore_content = """__pycache__
*.pyc
*.pyo
*.pyd
.Python
env
venv
.venv
pip-wheel-metadata
.eggs
*.egg-info
.git
.mypy_cache
.tox
.build
"""
    with open(".ruffignore", "w") as f:
        f.write(ignore_content)
    print("Created .ruffignore")

def create_gitignore_update():
    """Ensure black and ruff artifacts are in .gitignore."""
    gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv/
*.egg-info/
dist/
build/

# IDE
.idea/
.vscode/
*.swp
*.swo

# Testing
.pytest_cache/
.coverage
htmlcov/

# Ruff/Black
.ruff_cache/
"""
    
    if os.path.exists(".gitignore"):
        with open(".gitignore", "r") as f:
            existing = f.read()
        if ".ruff_cache/" not in existing:
            with open(".gitignore", "a") as f:
                f.write("\n# Ruff\n.ruff_cache/\n")
            print("Updated .gitignore with ruff cache")
        else:
            print(".gitignore already contains ruff cache entry")
    else:
        with open(".gitignore", "w") as f:
            f.write(gitignore_content)
        print("Created .gitignore with linting artifacts")

def main():
    """Main entry point for linting setup."""
    print("Setting up linting and formatting tools...")
    create_linting_config()
    create_formatting_config()
    create_ruffignore()
    create_gitignore_update()
    print("Linting and formatting configuration complete!")
    print("\nTo run linter: ruff check .")
    print("To run formatter: black .")
    print("To check formatting: black --check .")

if __name__ == "__main__":
    main()