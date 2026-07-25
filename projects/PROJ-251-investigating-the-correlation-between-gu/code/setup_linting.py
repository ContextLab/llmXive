"""
Setup script for linting and formatting tools.
This script configures ruff (linting) and black (formatting) for the project.
"""
import os
import sys
from pathlib import Path
import subprocess

def create_config_files():
    """Create configuration files for ruff and black."""
    root = Path(__file__).resolve().parent.parent
    
    # Create pyproject.toml if it doesn't exist, or append black config
    pyproject_path = root / "pyproject.toml"
    
    black_config = """
[tool.black]
line-length = 88
target-version = ['py311']
include = '\\.pyi?$'
exclude = '''
/(
    \\.git
    | \\.mypy_cache
    | \\.pytest_cache
    | build
    | dist
    | \\.eggs
)/
'''

[tool.ruff]
line-length = 88
target-version = "py311"
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # pyflakes
    "I",  # isort
    "C",  # flake8-comprehensions
    "B",  # flake8-bugbear
]
ignore = [
    "E501",  # line too long (handled by black)
    "B008",  # do not perform function calls in argument defaults
    "C901",  # too complex
]

[tool.ruff.per-file-ignores]
"__init__.py" = ["F401"]  # Allow unused imports in __init__.py

[tool.ruff.isort]
known-first-party = ["code"]
"""
    
    if not pyproject_path.exists():
        pyproject_path.write_text(black_config.strip())
        print(f"Created {pyproject_path}")
    else:
        # Check if black config already exists
        content = pyproject_path.read_text()
        if "[tool.black]" not in content:
            pyproject_path.write_text(content + "\n" + black_config)
            print(f"Updated {pyproject_path} with Black config")
        else:
            print(f"{pyproject_path} already contains Black config")
    
    # Create .ruff.toml for more detailed ruff configuration
    ruff_config_path = root / ".ruff.toml"
    ruff_config = """
# Ruff configuration file
target-version = "py311"
line-length = 88

[lint]
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # pyflakes
    "I",  # isort
    "C",  # flake8-comprehensions
    "B",  # flake8-bugbear
]
ignore = [
    "E501",  # line too long (handled by black)
    "B008",  # do not perform function calls in argument defaults
    "C901",  # too complex
]

[lint.per-file-ignores]
"__init__.py" = ["F401"]  # Allow unused imports in __init__.py

[lint.isort]
known-first-party = ["code"]
"""
    
    if not ruff_config_path.exists():
        ruff_config_path.write_text(ruff_config)
        print(f"Created {ruff_config_path}")
    else:
        print(f"{ruff_config_path} already exists")
    
    # Create .flake8 for backward compatibility
    flake8_config_path = root / ".flake8"
    flake8_config = """
[flake8]
max-line-length = 88
exclude = .git,__pycache__,build,dist,.eggs,.mypy_cache,.pytest_cache
ignore = E501,W503
"""
    
    if not flake8_config_path.exists():
        flake8_config_path.write_text(flake8_config)
        print(f"Created {flake8_config_path}")
    else:
        print(f"{flake8_config_path} already exists")
    
    # Create .gitignore entries for linting artifacts if not present
    gitignore_path = root / ".gitignore"
    gitignore_content = """
# Linting and formatting artifacts
.ruff_cache/
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
"""
    
    if gitignore_path.exists():
        existing = gitignore_path.read_text()
        if ".ruff_cache/" not in existing:
            gitignore_path.write_text(existing + "\n" + gitignore_content)
            print(f"Updated {gitignore_path} with linting artifacts")
    else:
        gitignore_path.write_text(gitignore_content)
        print(f"Created {gitignore_path}")

def main():
    """Main entry point for setup_linting script."""
    print("Setting up linting and formatting tools...")
    create_config_files()
    
    # Check if ruff and black are installed
    try:
        subprocess.run([sys.executable, "-m", "ruff", "--version"], 
                     check=True, capture_output=True)
        print("✓ Ruff is installed")
    except subprocess.CalledProcessError:
        print("⚠ Ruff is not installed. Install with: pip install ruff")
    
    try:
        subprocess.run([sys.executable, "-m", "black", "--version"], 
                     check=True, capture_output=True)
        print("✓ Black is installed")
    except subprocess.CalledProcessError:
        print("⚠ Black is not installed. Install with: pip install black")
    
    print("Linting and formatting configuration complete.")

if __name__ == "__main__":
    main()