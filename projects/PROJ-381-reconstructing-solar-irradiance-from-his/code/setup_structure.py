"""
Project structure initialization script.
Creates the required directory hierarchy and placeholder files.
"""
import os
from pathlib import Path
from typing import List

def create_structure() -> None:
    """
    Creates the project directory structure and necessary placeholder files.
    
    Directories created:
    - code/
    - code/models/
    - code/analysis/
    - code/data/
    - tests/
    - data/raw/
    - data/processed/
    - contracts/
    
    Files created:
    - __init__.py in all Python package directories
    - .gitkeep in data directories
    - requirements.txt
    - pyproject.toml (for black/ruff config)
    - .ruff.toml
    """
    root = Path(".")
    
    # Define directories to create
    directories: List[Path] = [
        root / "code",
        root / "code" / "models",
        root / "code" / "analysis",
        root / "code" / "data",
        root / "tests",
        root / "data" / "raw",
        root / "data" / "processed",
        root / "contracts",
    ]
    
    # Create directories
    for dir_path in directories:
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path}")
    
    # Define __init__.py files
    init_files: List[Path] = [
        root / "code" / "__init__.py",
        root / "code" / "models" / "__init__.py",
        root / "code" / "analysis" / "__init__.py",
        root / "code" / "data" / "__init__.py",
        root / "tests" / "__init__.py",
    ]
    
    # Create __init__.py files
    for init_file in init_files:
        init_file.write_text("")
        print(f"Created file: {init_file}")
    
    # Create .gitkeep files
    gitkeep_files: List[Path] = [
        root / "data" / "raw" / ".gitkeep",
        root / "data" / "processed" / ".gitkeep",
    ]
    
    for gitkeep in gitkeep_files:
        gitkeep.write_text("")
        print(f"Created file: {gitkeep}")
    
    # Create requirements.txt
    requirements_content = """# Core data processing and analysis
pandas>=2.0.0
numpy>=1.24.0
scipy>=1.10.0

# Machine learning
scikit-learn>=1.3.0

# Data handling
pyyaml>=6.0
requests>=2.31.0
joblib>=1.3.0

# Formatting and linting
black>=23.0.0
ruff>=0.1.0
"""
    requirements_file = root / "requirements.txt"
    requirements_file.write_text(requirements_content)
    print(f"Created file: {requirements_file}")
    
    # Create pyproject.toml for black configuration
    pyproject_content = """[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "solar-irradiance-reconstruction"
version = "0.1.0"
description = "Reconstructing Solar Irradiance from Historical Sunspot Records"
requires-python = ">=3.11"
dependencies = [
    "pandas>=2.0.0",
    "numpy>=1.24.0",
    "scipy>=1.10.0",
    "scikit-learn>=1.3.0",
    "pyyaml>=6.0",
    "requests>=2.31.0",
    "joblib>=1.3.0",
]

[tool.black]
line-length = 88
target-version = ['py311']
include = '\\.pyi?$'
exclude = '''
/(
    \.git
    | \.hg
    | \.mypy_cache
    | \.tox
    | \.venv
    | _build
    | buck-out
    | build
    | dist
)/
'''

[tool.ruff]
line-length = 88
target-version = "py311"
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # Pyflakes
    "I",  # isort
    "B",  # flake8-bugbear
    "C4", # flake8-comprehensions
]
ignore = [
    "E501", # line too long (handled by black)
    "B008", # do not perform function calls in argument defaults
]

[tool.ruff.isort]
known-first-party = ["code"]
"""
    pyproject_file = root / "pyproject.toml"
    pyproject_file.write_text(pyproject_content)
    print(f"Created file: {pyproject_file}")
    
    # Create .ruff.toml for explicit ruff configuration
    ruff_content = """# Ruff configuration
line-length = 88
target-version = "py311"

[lint]
select = [
    "E",
    "W",
    "F",
    "I",
    "B",
    "C4",
]
ignore = [
    "E501",
    "B008",
]

[lint.isort]
known-first-party = ["code"]
"""
    ruff_file = root / ".ruff.toml"
    ruff_file.write_text(ruff_content)
    print(f"Created file: {ruff_file}")
    
    print("\nProject structure initialized successfully!")

if __name__ == "__main__":
    create_structure()