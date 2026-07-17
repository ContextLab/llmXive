"""
Linting and formatting configuration setup script.

This script generates configuration files for flake8 and black to ensure
consistent code quality and formatting across the project.
"""
import os
import sys
from pathlib import Path

def check_config_files() -> bool:
    """
    Check if linting and formatting configuration files exist.
    
    Returns:
        bool: True if all required config files exist, False otherwise.
    """
    project_root = Path(__file__).resolve().parent.parent
    config_files = [
        project_root / "setup.cfg",
        project_root / ".flake8",
        project_root / "pyproject.toml",
    ]
    
    missing = [f for f in config_files if not f.exists()]
    
    if missing:
        print(f"Missing configuration files: {missing}")
        return False
    
    print("All linting and formatting configuration files exist.")
    return True

def main() -> int:
    """
    Main entry point for the setup_linting script.
    
    Returns:
        int: Exit code (0 for success, 1 for failure).
    """
    project_root = Path(__file__).resolve().parent.parent
    
    # Create setup.cfg with flake8 configuration
    setup_cfg_content = """[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude = 
    .git,
    __pycache__,
    build,
    dist,
    .eggs,
    *.egg-info
max-complexity = 10
per-file-ignores =
    # Ignore unused imports in __init__.py
    __init__.py:F401

[isort]
profile = black
multi_line_output = 3
include_trailing_comma = true
force_grid_wrap = 0
use_parentheses = true
ensure_newline_before_comments = true
line_length = 88
known_first_party = utils, data, tests

[black]
line-length = 88
target-version = py311
exclude = 
    .git
    __pycache__
    build
    dist
    .eggs
    *.egg-info
"""
    
    setup_cfg_path = project_root / "setup.cfg"
    with open(setup_cfg_path, "w") as f:
        f.write(setup_cfg_content)
    print(f"Created {setup_cfg_path}")
    
    # Create .flake8 file (alternative config for flake8)
    flake8_content = """[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude = 
    .git,
    __pycache__,
    build,
    dist,
    .eggs,
    *.egg-info
max-complexity = 10
"""
    
    flake8_path = project_root / ".flake8"
    with open(flake8_path, "w") as f:
        f.write(flake8_content)
    print(f"Created {flake8_path}")
    
    # Create pyproject.toml with Black and isort configuration
    pyproject_content = """[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "molecular-flexibility-permeability"
version = "0.1.0"
description = "Exploring the correlation between molecular flexibility and drug transport"
requires-python = ">=3.11"
dependencies = [
    "rdkit",
    "pandas",
    "scikit-learn",
    "matplotlib",
    "seaborn",
    "requests",
    "numpy",
    "scipy",
    "pyyaml",
]

[tool.black]
line-length = 88
target-version = ['py311']
include = '\\.pyi?$'
extend-exclude = '''
/(
    .git
    | __pycache__
    | build
    | dist
    | .eggs
    | .*\\.egg-info
)/
'''

[tool.isort]
profile = "black"
multi_line_output = 3
include_trailing_comma = true
force_grid_wrap = 0
use_parentheses = true
ensure_newline_before_comments = true
line_length = 88
known_first_party = ["utils", "data", "tests"]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
addopts = "-v --tb=short"

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
ignore_missing_imports = true
"""
    
    pyproject_path = project_root / "pyproject.toml"
    with open(pyproject_path, "w") as f:
        f.write(pyproject_content)
    print(f"Created {pyproject_path}")
    
    # Create .gitignore entries for linting artifacts if not present
    gitignore_path = project_root / ".gitignore"
    gitignore_entries = [
        ".flake8",
        ".mypy_cache/",
        "__pycache__/",
        "*.pyc",
        "*.pyo",
        "*.pyd",
        ".pytest_cache/",
        ".coverage",
        "htmlcov/",
        ".tox/",
        "dist/",
        "build/",
        "*.egg-info/",
    ]
    
    if gitignore_path.exists():
        with open(gitignore_path, "r") as f:
            existing_content = f.read()
        for entry in gitignore_entries:
            if entry not in existing_content:
                with open(gitignore_path, "a") as f:
                    f.write(f"\n{entry}\n")
        print("Updated .gitignore with linting-related entries.")
    else:
        with open(gitignore_path, "w") as f:
            f.write("\n".join(gitignore_entries) + "\n")
        print("Created .gitignore with linting-related entries.")
    
    print("\nLinting and formatting configuration complete.")
    print("To run flake8: flake8 code/")
    print("To run black: black code/")
    print("To run isort: isort code/")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())