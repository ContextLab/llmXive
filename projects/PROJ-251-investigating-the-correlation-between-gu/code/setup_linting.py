"""
Linting and Formatting Setup Module.

This module provides utilities to generate configuration files for
Ruff (linting) and Black (formatting) to ensure code consistency.
"""
import os
from pathlib import Path


def create_config_files(project_root: Path) -> None:
    """
    Create configuration files for Ruff and Black in the project root.

    Args:
        project_root: The root directory of the project.
    """
    # Ensure the project root exists
    project_root.mkdir(parents=True, exist_ok=True)

    # 1. Create .ruff.toml for Ruff linting configuration
    ruff_config_path = project_root / ".ruff.toml"
    if not ruff_config_path.exists():
        ruff_content = """
# Ruff configuration file
target-version = "py311"
line-length = 88

[lint]
# Select specific rules
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
    "E501", # Line too long (handled by Black)
    "B008", # Do not perform function call in argument defaults (common in data pipelines)
]

[lint.isort]
known-first-party = ["utils", "tests"]
known-third-party = ["pandas", "numpy", "scipy", "sklearn", "yaml", "requests", "biom", "qiime2", "dada2"]

[format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "auto"
"""
        ruff_config_path.write_text(ruff_content.strip())
        print(f"Created {ruff_config_path}")
    else:
        print(f"Skipped {ruff_config_path} (already exists)")

    # 2. Create .black configuration in pyproject.toml
    pyproject_path = project_root / "pyproject.toml"
    
    # Read existing content if file exists
    existing_content = ""
    if pyproject_path.exists():
        existing_content = pyproject_path.read_text()

    # Define the black section
    black_section = """
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
"""

    # Check if [tool.black] already exists
    if "[tool.black]" in existing_content:
        print(f"Skipped updating [tool.black] in {pyproject_path} (already exists)")
    else:
        # Append to existing content
        new_content = existing_content.rstrip() + "\n" + black_section
        pyproject_path.write_text(new_content)
        print(f"Updated {pyproject_path} with [tool.black] section")

    # 3. Create .flake8 if preferred (optional, but requested in task)
    # We will create it to satisfy the "ruff/flake8" requirement, even if ruff is primary.
    flake8_config_path = project_root / ".flake8"
    if not flake8_config_path.exists():
        flake8_content = """
[flake8]
max-line-length = 88
exclude = .git,__pycache__,build,dist
ignore = E501,W503
"""
        flake8_config_path.write_text(flake8_content.strip())
        print(f"Created {flake8_config_path}")
    else:
        print(f"Skipped {flake8_config_path} (already exists)")

    print("Linting and formatting configuration files created successfully.")


if __name__ == "__main__":
    # Run as a script to generate configs in the current directory
    create_config_files(Path("."))