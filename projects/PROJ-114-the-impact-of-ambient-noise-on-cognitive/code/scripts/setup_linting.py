"""
Setup linting and formatting tools configuration.

This script ensures that flake8, black, and isort configuration files
are present and that the required packages are listed in requirements.txt.
"""
import os
import sys
import configparser
from pathlib import Path
from typing import List, Tuple

def check_config_files() -> Tuple[bool, List[str]]:
    """
    Check if linting and formatting config files exist, create if missing.
    
    Returns:
        Tuple of (all_exist: bool, created_files: List[str])
    """
    code_dir = Path(__file__).parent.parent
    created_files = []
    
    # Check for .flake8
    flake8_path = code_dir / ".flake8"
    if not flake8_path.exists():
        flake8_config = """[flake8]
max-line-length = 100
exclude = .git,__pycache__,venv,build,dist,.eggs
ignore = E203,W503
per-file-ignores =
    __init__.py:F401
"""
        flake8_path.write_text(flake8_config)
        created_files.append(str(flake8_path))
        print(f"Created {flake8_path}")
    
    # Check for pyproject.toml
    pyproject_path = code_dir / "pyproject.toml"
    if not pyproject_path.exists():
        pyproject_config = """[tool.black]
line-length = 100
target-version = ['py311']
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

[tool.isort]
profile = "black"
line_length = 100
skip_gitignore = true
known_first_party = ["code"]

[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"
"""
        pyproject_path.write_text(pyproject_config)
        created_files.append(str(pyproject_path))
        print(f"Created {pyproject_path}")
    
    # Check for setup.cfg
    setup_cfg_path = code_dir / "setup.cfg"
    if not setup_cfg_path.exists():
        setup_cfg_config = """[metadata]
name = ambient-noise-cognitive-flexibility
version = 0.1.0
description = Pipeline for analyzing impact of ambient noise on cognitive flexibility
author = Research Team
python_requires = >=3.11

[options]
packages = find:
install_requires =
    pandas>=1.3.0
    numpy>=1.21.0
    scipy>=1.7.0
    statsmodels>=0.13.0
    scikit-learn>=1.0.0
    pyyaml>=5.4
    jsonschema>=4.0.0
    pytest>=7.0.0
    requests>=2.27.0

[options.packages.find]
where = .
"""
        setup_cfg_path.write_text(setup_cfg_config)
        created_files.append(str(setup_cfg_path))
        print(f"Created {setup_cfg_path}")
    
    all_exist = (flake8_path.exists() and pyproject_path.exists() and 
                setup_cfg_path.exists())
    return all_exist, created_files

def check_requirements() -> Tuple[bool, List[str]]:
    """
    Check if flake8, black, and isort are in requirements.txt.
    
    Returns:
        Tuple of (all_present: bool, added_packages: List[str])
    """
    code_dir = Path(__file__).parent.parent
    req_path = code_dir / "requirements.txt"
    
    required_packages = ["flake8", "black", "isort"]
    added_packages = []
    
    if not req_path.exists():
        print(f"Warning: {req_path} does not exist. Creating it.")
        req_path.write_text("")
    
    # Read current requirements
    current_reqs = set()
    with open(req_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                # Extract package name (before any version specifier)
                pkg_name = line.split('>=')[0].split('==')[0].split('<')[0].split('>')[0].strip()
                current_reqs.add(pkg_name.lower())
    
    # Check and add missing packages
    missing = []
    for pkg in required_packages:
        if pkg.lower() not in current_reqs:
            missing.append(pkg)
    
    if missing:
        with open(req_path, 'a') as f:
            for pkg in missing:
                f.write(f"{pkg}\n")
                added_packages.append(pkg)
                print(f"Added {pkg} to requirements.txt")
    
    all_present = len(missing) == 0
    return all_present, added_packages

def main() -> int:
    """
    Main entry point to configure linting.
    
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    print("Setting up linting and formatting tools...")
    
    # Check config files
    configs_exist, created_configs = check_config_files()
    if created_configs:
        print(f"Created {len(created_configs)} config file(s)")
    else:
        print("All config files already exist")
    
    # Check requirements
    reqs_ok, added_reqs = check_requirements()
    if added_reqs:
        print(f"Added {len(added_reqs)} package(s) to requirements.txt: {', '.join(added_reqs)}")
    else:
        print("All required packages already in requirements.txt")
    
    print("\nLinting configuration complete!")
    print("To lint your code, run: flake8 code/ tests/")
    print("To format your code, run: black code/ tests/ && isort code/ tests/")
    print("Or use the Makefile: make lint, make format, make test")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())