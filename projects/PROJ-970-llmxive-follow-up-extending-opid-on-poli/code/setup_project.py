import sys
import importlib
import os
import subprocess

def check_dependency(package_name: str, import_name: str = None) -> bool:
    """
    Check if a package is installed and can be imported.
    If import_name is None, it defaults to package_name.
    """
    if import_name is None:
        import_name = package_name
    
    try:
        importlib.import_module(import_name)
        return True
    except ImportError:
        return False

def create_project_structure():
    """
    Creates the standard directory structure for the llmXive project.
    """
    dirs = [
        "code",
        "code/agent",
        "code/env",
        "code/experiments",
        "code/utils",
        "data",
        "data/raw",
        "data/raw/synthetic_graphs",
        "data/processed",
        "data/figures",
        "tests",
        "tests/agent",
        "tests/env",
        "tests/experiments",
        "tests/utils",
        "specs",
        "specs/001-opid-routing-complexity",
        "docs",
        "logs"
    ]
    
    for d in dirs:
        os.makedirs(d, exist_ok=True)
        # Create __init__.py in code and tests directories to make them packages
        if d.startswith("code") and d != "code":
            init_path = os.path.join(d, "__init__.py")
            if not os.path.exists(init_path):
                with open(init_path, "w") as f:
                    f.write("# llmXive code package\n")
        elif d.startswith("tests"):
            init_path = os.path.join(d, "__init__.py")
            if not os.path.exists(init_path):
                with open(init_path, "w") as f:
                    f.write("# llmXive tests package\n")

def create_requirements_txt():
    """
    Creates the requirements.txt file with necessary dependencies.
    """
    deps = [
        "networkx>=3.2",
        "numpy>=1.24",
        "pandas>=2.0",
        "scipy>=1.11",
        "pytest>=7.4",
        "ruff>=0.1.0",
        "black>=23.0"
    ]
    
    with open("requirements.txt", "w") as f:
        f.write("\n".join(deps) + "\n")

def create_pyproject_toml():
    """
    Creates a basic pyproject.toml for project metadata and tool configuration.
    """
    content = """[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "llmxive-opid-routing"
version = "0.1.0"
description = "OPID Critical-First Routing Complexity Analysis"
requires-python = ">=3.11"
dependencies = [
    "networkx>=3.2",
    "numpy>=1.24",
    "pandas>=2.0",
    "scipy>=1.11",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4",
    "ruff>=0.1.0",
    "black>=23.0",
]

[tool.black]
line-length = 88
target-version = ['py311']

[tool.ruff]
line-length = 88
target-version = "py311"
select = ["E", "F", "W", "I"]
ignore = []

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
"""
    with open("pyproject.toml", "w") as f:
        f.write(content)

def main():
    print("Initializing llmXive project structure...")
    
    # 1. Create directory structure
    create_project_structure()
    print("✓ Directory structure created.")
    
    # 2. Create requirements.txt
    create_requirements_txt()
    print("✓ requirements.txt created.")
    
    # 3. Create pyproject.toml
    create_pyproject_toml()
    print("✓ pyproject.toml created.")
    
    print("\nProject structure initialized successfully.")
    print("Next steps:")
    print("  1. Run: python -m venv venv")
    print("  2. Run: source venv/bin/activate (or venv\\Scripts\\activate on Windows)")
    print("  3. Run: pip install -r requirements.txt")

if __name__ == "__main__":
    main()