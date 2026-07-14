"""
Setup script for linting and formatting tools (Ruff, Black).
This script ensures configuration files exist in the project root.
"""
import os
from pathlib import Path
import sys

from setup_dirs import get_project_root

def ensure_config_files(root: Path) -> None:
    """Create or verify existence of .ruff.toml, pyproject.toml (black/pytest), and .gitignore."""
    
    files_to_check = {
        ".ruff.toml": """[lint]
select = ["E", "F", "I", "W"]
ignore = []
fixable = ["ALL"]
unfixable = []
exclude = [
    ".bzr", ".direnv", ".eggs", ".git", ".git-rewrite", ".hg", ".mypy_cache",
    ".nox", ".pants.d", ".pytype", ".ruff_cache", ".svn", ".tox", ".venv",
    "__pypackages__", "_build", "buck-out", "build", "dist", "node_modules", "venv",
]
line-length = 88
target-version = "py311"
""",
        "pyproject.toml": """[project]
name = "quantifying-the-impact-of-data-artifacts"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "numpy", "scikit-image", "astropy", "scipy", "statsmodels", "pandas", "matplotlib", "pytest"
]

[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[tool.black]
line-length = 88
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

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
addopts = "-v"

[tool.ruff]
line-length = 88
target-version = "py311"
""",
        ".gitignore": """# Python
__pycache__/
*.py[cod]
$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Logs
*.log
logs/

# Data
data/

# IDE
.idea/
.vscode/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Testing
.pytest_cache/
.coverage
htmlcov/

# Environment
.venv/
venv/
ENV/

# Jupyter
.ipynb_checkpoints
""",
        "README.md": """# Quantifying the Impact of Data Artifacts on Planetary Nebula Morphology

## Overview
This project implements an automated science pipeline to quantify how instrumental data artifacts (specifically noise and saturation) bias the measurement of planetary nebula morphology (ellipticity and asymmetry).

## Quickstart
1. Install dependencies: `pip install -r requirements.txt`
2. Run pipeline: `python code/main.py`
3. Run tests: `pytest`
4. Lint: `ruff check .`
5. Format: `black .`
""",
        "requirements.txt": """numpy>=1.26.0
scikit-image>=0.22.0
astropy>=6.0.0
scipy>=1.12.0
statsmodels>=0.14.0
pandas>=2.2.0
matplotlib>=3.8.0
pytest>=8.0.0
ruff>=0.3.0
black>=24.0.0
"""
    }

    for filename, content in files_to_check.items():
        file_path = root / filename
        if not file_path.exists():
            print(f"Creating {file_path}...")
            file_path.write_text(content.strip() + "\n")
        else:
            print(f"{filename} already exists.")

def main() -> int:
    """Main entry point for setup_linting."""
    root = get_project_root()
    print(f"Project root: {root}")
    ensure_config_files(root)
    print("Linting and formatting configuration complete.")
    return 0

if __name__ == "__main__":
    sys.exit(main())