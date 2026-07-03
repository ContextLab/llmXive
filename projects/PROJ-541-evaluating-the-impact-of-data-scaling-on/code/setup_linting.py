import os
import sys
import subprocess
from pathlib import Path

def main():
    """
    Configure linting (ruff, flake8) and formatting (black) tools.
    This script ensures configuration files are present and dependencies are installed.
    """
    project_root = Path(__file__).resolve().parent.parent
    code_dir = project_root / "code"
    
    # Ensure code directory exists
    code_dir.mkdir(exist_ok=True)
    
    # 1. Install dependencies if not present (optional but helpful for verification)
    # We assume requirements.txt was handled in T002, but we can verify or add here if needed.
    # For this task, we focus on configuration files.

    # 2. Create .ruff.toml
    ruff_config = code_dir / ".ruff.toml"
    if not ruff_config.exists():
        ruff_content = """
# Ruff configuration for llmXive project
target-version = "py311"
line-length = 88

[lint]
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
    "E501", # Line too long (handled by black)
    "B008", # Do not perform function call in argument defaults (common in dataclasses)
]

[lint.isort]
known-first-party = ["simulation", "preprocessing", "analysis", "visualization", "utils", "tests", "main"]
"""
        with open(ruff_config, "w") as f:
            f.write(ruff_content.strip())
        print(f"Created: {ruff_config}")
    else:
        print(f"Exists: {ruff_config}")

    # 3. Create .flake8
    flake8_config = code_dir / ".flake8"
    if not flake8_config.exists():
        flake8_content = """
[flake8]
max-line-length = 88
exclude = .git,__pycache__,build,dist
ignore = E501,B008
"""
        with open(flake8_config, "w") as f:
            f.write(flake8_content.strip())
        print(f"Created: {flake8_config}")
    else:
        print(f"Exists: {flake8_config}")

    # 4. Create pyproject.toml with Black configuration
    # We append to existing or create new if it doesn't exist
    pyproject = project_root / "pyproject.toml"
    black_section = """
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
"""
    
    needs_update = True
    if pyproject.exists():
        with open(pyproject, "r") as f:
            content = f.read()
            if "[tool.black]" in content:
                print(f"Black config already exists in {pyproject}")
                needs_update = False
    
    if needs_update:
        with open(pyproject, "a") as f:
            f.write("\n" + black_section.strip())
        print(f"Updated: {pyproject} with Black config")
    else:
        print(f"Skipped update: {pyproject}")

    print("Linting and formatting tools configured successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())