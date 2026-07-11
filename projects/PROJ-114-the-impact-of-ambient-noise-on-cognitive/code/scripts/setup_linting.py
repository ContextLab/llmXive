"""
Script to verify linting and formatting configuration.
This script ensures that flake8, black, and isort are correctly configured
and can be run against the project codebase.

Usage:
    python code/scripts/setup_linting.py
    
This script does not modify files but validates that the configuration
files (.flake8, pyproject.toml) are present and parseable.
"""
import os
import sys
import configparser
import toml
from pathlib import Path

def check_config_files():
    """Verify that configuration files exist and are valid."""
    project_root = Path(__file__).parent.parent.parent
    
    # Check .flake8
    flake8_path = project_root / ".flake8"
    if not flake8_path.exists():
        print("ERROR: .flake8 configuration file not found.")
        return False
    
    try:
        config = configparser.ConfigParser()
        config.read(flake8_path)
        if 'flake8' not in config:
            print("ERROR: [flake8] section missing in .flake8")
            return False
        print(f"✓ .flake8 configuration valid: {flake8_path}")
    except Exception as e:
        print(f"ERROR: Failed to parse .flake8: {e}")
        return False

    # Check pyproject.toml for black/isort/mypy
    pyproject_path = project_root / "pyproject.toml"
    if not pyproject_path.exists():
        print("ERROR: pyproject.toml configuration file not found.")
        return False
    
    try:
        with open(pyproject_path, 'r', encoding='utf-8') as f:
            pyproject = toml.load(f)
        
        if 'tool' not in pyproject:
            print("ERROR: [tool] section missing in pyproject.toml")
            return False
        
        tools = pyproject['tool']
        if 'black' not in tools:
            print("WARNING: [tool.black] section missing in pyproject.toml")
        else:
            print(f"✓ Black configuration valid: {pyproject_path}")
            
        if 'isort' not in tools:
            print("WARNING: [tool.isort] section missing in pyproject.toml")
        else:
            print(f"✓ Isort configuration valid: {pyproject_path}")
            
        if 'mypy' not in tools:
            print("WARNING: [tool.mypy] section missing in pyproject.toml")
        else:
            print(f"✓ MyPy configuration valid: {pyproject_path}")
            
    except Exception as e:
        print(f"ERROR: Failed to parse pyproject.toml: {e}")
        return False

    return True

def check_requirements():
    """Verify that linting dependencies are listed in requirements.txt."""
    project_root = Path(__file__).parent.parent.parent
    req_path = project_root / "requirements.txt"
    
    if not req_path.exists():
        print("WARNING: requirements.txt not found. Skipping dependency check.")
        return True
    
    try:
        with open(req_path, 'r', encoding='utf-8') as f:
            content = f.read().lower()
        
        required_packages = ['flake8', 'black', 'isort', 'mypy']
        missing = []
        
        for pkg in required_packages:
            if pkg not in content:
                missing.append(pkg)
        
        if missing:
            print(f"ERROR: Missing linting dependencies in requirements.txt: {missing}")
            return False
        
        print(f"✓ All linting dependencies present in requirements.txt")
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to read requirements.txt: {e}")
        return False

def main():
    print("Verifying Linting and Formatting Configuration...")
    print("-" * 50)
    
    success = True
    success &= check_config_files()
    success &= check_requirements()
    
    print("-" * 50)
    if success:
        print("SUCCESS: Linting configuration is ready.")
        print("Run 'python -m flake8 code/' to check for style issues.")
        print("Run 'python -m black --check code/' to verify formatting.")
        print("Run 'python -m isort --check-only code/' to verify import order.")
        return 0
    else:
        print("FAILURE: Configuration issues detected. Please fix the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())