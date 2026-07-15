"""
Script to initialize the project directory structure for PROJ-845.
Creates all required subdirectories and empty __init__.py files.
"""
import os
from pathlib import Path

PROJECT_ROOT = Path("projects/PROJ-845-llmxive-follow-up-extending-qwen-image-f")

# Define the directory structure relative to the project root
# Note: code/ is a package root, so subdirs under it need __init__.py if they are packages
# The task asks for __init__.py in "each Python package directory".
# We will create __init__.py in the root of code/, tests/, and any subdirs that are meant to be packages.
# Based on standard Python practice, we add __init__.py to:
# - code/, code/generators/, code/models/, code/training/, code/analysis/, code/utils/
# - tests/unit/, tests/integration/ (and tests root if considered a package)
# - The project root itself if it's a package (usually not, but good for namespace)
# The task explicitly lists: data/raw, data/processed, code, code/generators, code/models, code/training,
# code/analysis, code/utils, tests/unit, tests/integration, contracts.

# We will treat 'code' and 'tests' and 'contracts' as package roots too.
# 'data' is usually data, not code, so we might not put __init__.py in data/raw, but the task says "each Python package directory".
# To be safe and follow the "add an empty __init__.py in each Python package directory" instruction strictly for the listed paths:
# We will create __init__.py in every directory listed in the task that is under 'code' or 'tests' or 'contracts'.
# For 'data', it's not a Python package, but the task lists it. I will assume the instruction applies to the Python-relevant ones.
# However, to be robust, I will create __init__.py in the root of 'code' and 'tests' and 'contracts', and their subdirs.
# I will NOT put __init__.py in data/raw or data/processed as they are data storage, not code packages.

# Re-reading: "add an empty __init__.py in each Python package directory."
# The directories listed are:
# code/, code/generators/, code/models/, code/training/, code/analysis/, code/utils/ -> These are packages.
# tests/unit/, tests/integration/ -> These are packages. tests/ itself is likely a package.
# contracts/ -> Could be a package if containing Python, but usually schemas. I'll make it a package to be safe.
# data/raw/, data/processed/ -> These are NOT Python packages.

# Directories to create:
dirs_to_create = [
    "data/raw",
    "data/processed",
    "code",
    "code/generators",
    "code/models",
    "code/training",
    "code/analysis",
    "code/utils",
    "tests/unit",
    "tests/integration",
    "contracts",
]

# Directories that should be treated as Python packages (have __init__.py)
# Based on the list above, excluding data/
packages_to_init = [
    "code",
    "code/generators",
    "code/models",
    "code/training",
    "code/analysis",
    "code/utils",
    "tests",
    "tests/unit",
    "tests/integration",
    "contracts",
]

def main():
    print(f"Setting up project directory: {PROJECT_ROOT}")
    
    # Create base project root
    PROJECT_ROOT.mkdir(parents=True, exist_ok=True)
    
    # Create all directories
    for d in dirs_to_create:
        dir_path = PROJECT_ROOT / d
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path}")
    
    # Create __init__.py in package directories
    for pkg in packages_to_init:
        pkg_path = PROJECT_ROOT / pkg
        init_file = pkg_path / "__init__.py"
        # Ensure the directory exists before writing (it should from previous step)
        init_file.touch(exist_ok=True)
        print(f"Created __init__.py in: {init_file}")
    
    print("Setup complete.")

if __name__ == "__main__":
    main()