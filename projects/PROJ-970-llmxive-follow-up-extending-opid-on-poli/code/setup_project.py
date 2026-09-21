import sys
import importlib
import os
import subprocess
from typing import List, Dict, Any, Optional

def check_dependency(package_name: str) -> bool:
    """Check if a package is installed."""
    try:
        importlib.import_module(package_name.replace("-", "_"))
        return True
    except ImportError:
        return False

def create_project_structure() -> None:
    """Create the required directory structure for the project."""
    # Define the directories to create relative to the project root
    # The project root is assumed to be the current working directory
    # or the directory where this script is run from.
    base_dir = os.getcwd()
    
    directories = [
        "src",
        "src/environment",
        "src/agent",
        "src/simulation",
        "src/analysis",
        "tests",
        "data/raw/synthetic_graphs",
        "data/processed",
        "docs",
        "figures"
    ]

    for dir_path in directories:
        full_path = os.path.join(base_dir, dir_path)
        if not os.path.exists(full_path):
            os.makedirs(full_path)
            print(f"Created directory: {full_path}")
        else:
            print(f"Directory already exists: {full_path}")

def create_requirements_txt() -> None:
    """Create a requirements.txt file with pinned versions."""
    requirements = [
        "networkx==3.2.1",
        "numpy==1.26.4",
        "pandas==2.2.1",
        "scipy==1.13.0",
        "pytest==8.1.1",
        "ruff==0.3.0",
        "black==24.3.0"
    ]
    
    base_dir = os.getcwd()
    file_path = os.path.join(base_dir, "requirements.txt")
    
    with open(file_path, "w") as f:
        f.write("# llmXive Project Requirements\n")
        for req in requirements:
            f.write(f"{req}\n")
    
    print(f"Created requirements.txt at {file_path}")

def create_pyproject_toml() -> None:
    """Create a pyproject.toml file for project metadata and tool configuration."""
    base_dir = os.getcwd()
    file_path = os.path.join(base_dir, "pyproject.toml")
    
    content = """[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "llmxive-opid-routing"
version = "0.1.0"
description = "OPID Critical-First Routing Complexity Analysis"
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "networkx==3.2.1",
    "numpy==1.26.4",
    "pandas==2.2.1",
    "scipy==1.13.0",
    "pytest==8.1.1",
]

[tool.setuptools]
packages = ["src", "src.environment", "src.agent", "src.simulation", "src.analysis", "tests"]

[tool.black]
line-length = 88
target-version = ['py311']

[tool.ruff]
line-length = 88
target-version = "py311"

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
python_classes = "Test*"
python_functions = "test_*"
"""
    
    with open(file_path, "w") as f:
        f.write(content)
    
    print(f"Created pyproject.toml at {file_path}")

def main() -> None:
    """Main entry point to set up the project."""
    print("Starting project setup...")
    
    # 1. Create directory structure
    create_project_structure()
    
    # 2. Create requirements.txt
    create_requirements_txt()
    
    # 3. Create pyproject.toml
    create_pyproject_toml()
    
    print("Project setup complete.")

if __name__ == "__main__":
    main()