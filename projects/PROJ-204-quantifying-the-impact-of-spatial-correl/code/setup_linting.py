"""
Setup script to initialize linting and formatting configuration files.
This script ensures .ruff.toml and .black.toml are present and valid.
"""
import os
from pathlib import Path

def create_config_files():
    """Create configuration files for ruff and black if they don't exist."""
    base_dir = Path(__file__).parent
    ruff_config = base_dir / ".ruff.toml"
    black_config = base_dir / ".black.toml"
    dev_req = base_dir / "requirements-dev.txt"

    ruff_content = """[lint]
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # Pyflakes
    "I",  # isort
    "B",  # flake8-bugbear
    "C4", # flake8-comprehensions
    "UP", # pyupgrade
]
ignore = [
    "E501", # line too long (handled by black)
    "B008", # do not perform function calls in argument defaults (common in data pipelines)
    "C901", # too complex (temporarily relaxed for initial implementation)
]
fixable = ["ALL"]
unfixable = []

[lint.isort]
known-first-party = ["analysis", "data", "preprocess", "modeling", "validation", "report", "utils", "setup_structure"]
force-sort-within-sections = true

[format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "auto"
"""

    black_content = """[tool.black]
line-length = 88
target-version = ['py39', 'py310', 'py311']
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
"""

    dev_req_content = """# Development and Tooling Dependencies
# Generated for PROJ-204-quantifying-the-impact-of-spatial-correl
# Task T003: Linting and Formatting Configuration

# Linting and Formatting
ruff>=0.1.0
black>=23.0.0
isort>=5.12.0

# Testing (if not already in main requirements)
pytest>=7.0.0
pytest-cov>=4.0.0
pytest-xdist>=3.0.0
"""

    if not ruff_config.exists():
        ruff_config.write_text(ruff_content)
        print(f"Created {ruff_config}")
    else:
        print(f"{ruff_config} already exists, skipping.")

    if not black_config.exists():
        black_config.write_text(black_content)
        print(f"Created {black_config}")
    else:
        print(f"{black_config} already exists, skipping.")

    if not dev_req.exists():
        dev_req.write_text(dev_req_content)
        print(f"Created {dev_req}")
    else:
        print(f"{dev_req} already exists, skipping.")

if __name__ == "__main__":
    create_config_files()
    print("Linting and formatting configuration complete.")