"""
Initialize the project with pyproject.toml for Python 3.11 configuration.
This script creates the standard project configuration file.
"""
import os
from pathlib import Path

def create_pyproject_toml():
    """Create a pyproject.toml file with project metadata and tool configurations."""
    content = """[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "llmxive-antibiotic-resistance"
version = "0.1.0"
description = "Predicting Antibiotic Resistance Evolution from Genomic Sequences"
requires-python = ">=3.11"
authors = [
    {name = "llmXive Research Team"}
]
dependencies = [
    "scikit-learn",
    "pandas",
    "numpy",
    "matplotlib",
    "seaborn",
    "biopython",
    "requests",
    "pyyaml",
    "dendropy",
    "statsmodels",
    "joblib",
    "scipy"
]

[project.optional-dependencies]
dev = [
    "pytest",
    "ruff",
    "black"
]

[tool.setuptools.packages.find]
where = ["code"]

[tool.black]
line-length = 88
target-version = ['py311']
include = '\\.pyi?$'

[tool.ruff]
line-length = 88
target-version = "py311"
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # pyflakes
    "I",  # isort
    "B",  # flake8-bugbear
    "C4", # flake8-comprehensions
]
ignore = [
    "E501", # line too long (handled by black)
    "B008", # do not perform function calls in argument defaults
]

[tool.ruff.per-file-ignores]
"__init__.py" = ["F401"]
"""
    
    root_dir = Path(__file__).parent.parent
    pyproject_path = root_dir / "pyproject.toml"
    
    with open(pyproject_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Created {pyproject_path}")
    return pyproject_path

def main():
    """Main entry point."""
    create_pyproject_toml()
    print("Project initialization complete.")

if __name__ == "__main__":
    main()