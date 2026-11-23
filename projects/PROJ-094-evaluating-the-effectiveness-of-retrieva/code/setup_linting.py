"""
Setup script to configure ruff (linting) and black (formatting) for the project.
Generates configuration files in the project root.
"""
import os
from pathlib import Path

def main():
    root = Path(__file__).resolve().parent.parent
    
    # 1. Create .ruff.toml
    ruff_config = """
[lint]
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # pyflakes
    "I",  # isort
    "B",  # flake8-bugbear
    "C4", # flake8-comprehensions
    "UP", # pyupgrade
]
ignore = [
    "E501", # line too long (handled by black)
    "B008", # do not perform function calls in argument defaults
]

[lint.isort]
known-first-party = ["src"]
known-third-party = ["ir_datasets", "sentence_transformers", "faiss", "rank_bm25", "sklearn", "pandas", "numpy", "psutil", "transformers", "torch", "accelerate"]

[format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "auto"
"""
    ruff_path = root / ".ruff.toml"
    ruff_path.write_text(ruff_config)
    print(f"Created: {ruff_path}")

    # 2. Create pyproject.toml [tool.black] section
    # Check if file exists to avoid overwriting existing config if any
    pyproject_path = root / "pyproject.toml"
    black_section = """
[tool.black]
line-length = 88
target-version = ['py39']
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
    
    if pyproject_path.exists():
        content = pyproject_path.read_text()
        if "[tool.black]" in content:
            print(f"Warning: [tool.black] section already exists in {pyproject_path}")
        else:
            pyproject_path.write_text(content + "\n" + black_section)
            print(f"Appended [tool.black] section to: {pyproject_path}")
    else:
        pyproject_path.write_text(black_section)
        print(f"Created: {pyproject_path}")

    # 3. Create .pre-commit-config.yaml for automated enforcement
    pre_commit_config = """
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.6.9
    hooks:
- id: ruff
  args: [--fix]
- id: ruff-format
  - repo: https://github.com/psf/black
    rev: 24.8.0
    hooks:
- id: black
  language_version: python3
"""
    pre_commit_path = root / ".pre-commit-config.yaml"
    pre_commit_path.write_text(pre_commit_config)
    print(f"Created: {pre_commit_path}")

    print("\nLinting and formatting tools configured successfully.")
    print("To run manually:")
    print("  ruff check .")
    print("  black .")
    print("To install pre-commit hooks:")
    print("  pip install pre-commit")
    print("  pre-commit install")

if __name__ == "__main__":
    main()