"""
Script to initialize pre-commit hooks for the project.
Creates the .pre-commit-config.yaml file.
"""
import os
from pathlib import Path

CONFIG_CONTENT = """repos:
  - repo: local
    hooks:
- id: check-large-files
  name: Check Large Files
  entry: python code/pre_commit_hooks/check_large_files.py
  language: python
  types: [file]
  pass_filenames: true
  exclude: '^data/'
  args: []
- id: check-inefficient-imports
  name: Check Inefficient Imports
  entry: python code/pre_commit_hooks/check_inefficient_imports.py
  language: python
  types: [python]
  pass_filenames: true
  exclude: '^venv/|^tests/'
  args: []
  - repo: https://github.com/psf/black
    rev: 23.1.0
    hooks:
- id: black
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.6
    hooks:
- id: ruff
  args: [--fix, --exit-non-zero-on-fix]
"""

def main():
    root = Path.cwd()
    config_path = root / ".pre-commit-config.yaml"
    
    if config_path.exists():
        print(f"Warning: {config_path} already exists. Overwriting.")
    
    with open(config_path, 'w') as f:
        f.write(CONFIG_CONTENT)
    
    print(f"Created {config_path}")
    print("Run 'pip install pre-commit' and then 'pre-commit install' to activate hooks.")
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())