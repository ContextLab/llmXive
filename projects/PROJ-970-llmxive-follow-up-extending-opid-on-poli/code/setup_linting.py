import os
import sys

def create_ruff_config() -> str:
    """Generate the .ruff.toml configuration file content."""
    return """[lint]
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # pyflakes
    "I",  # isort
    "B",  # flake8-bugbear
    "C4", # flake8-comprehensions
    "UP", # pyupgrade
    "N",  # pep8-naming
]
ignore = [
    "E501", # line-too-long (handled by black)
    "B008", # do not perform function calls in argument defaults
    "C901", # too complex
]

[lint.isort]
known-first-party = ["config", "env", "experiments", "utils"]
known-third-party = ["networkx", "numpy", "pandas", "scipy", "pytest"]

[format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "auto"
"""

def create_black_config() -> str:
    """Generate the pyproject.toml section for Black configuration."""
    # We append to an existing or new pyproject.toml
    # This function returns the specific section to append if pyproject.toml doesn't exist yet
    return """[tool.black]
line-length = 100
target-version = ['py311']
include = '\\.pyi?$'
exclude = '''
/(
    \.eggs
  | \.git
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
line-length = 100
target-version = "py311"
"""

def create_pre_commit_config() -> str:
    """Generate the .pre-commit-config.yaml content."""
    return """repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.6.9
    hooks:
- id: ruff
  args: [ --fix ]
- id: ruff-format
  - repo: https://github.com/psf/black
    rev: 24.8.0
    hooks:
- id: black
  language_version: python3.11
"""

def main():
    """Create linting and formatting configuration files in the project root."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Create .ruff.toml
    ruff_path = os.path.join(project_root, ".ruff.toml")
    if os.path.exists(ruff_path):
        print(f"[setup_linting] {ruff_path} already exists. Skipping.")
    else:
        with open(ruff_path, "w", encoding="utf-8") as f:
            f.write(create_ruff_config())
        print(f"[setup_linting] Created {ruff_path}")

    # Create/Append to pyproject.toml
    pyproject_path = os.path.join(project_root, "pyproject.toml")
    black_config = create_black_config()
    
    if os.path.exists(pyproject_path):
        with open(pyproject_path, "r", encoding="utf-8") as f:
            existing_content = f.read()
        
        # Simple check to avoid duplicating the [tool.black] section if it exists
        if "[tool.black]" in existing_content:
            print(f"[setup_linting] [tool.black] section already exists in {pyproject_path}. Skipping update.")
        else:
            with open(pyproject_path, "a", encoding="utf-8") as f:
                f.write("\n" + black_config)
            print(f"[setup_linting] Appended Black config to {pyproject_path}")
    else:
        with open(pyproject_path, "w", encoding="utf-8") as f:
            f.write(black_config)
        print(f"[setup_linting] Created {pyproject_path} with Black config")

    # Create .pre-commit-config.yaml
    pre_commit_path = os.path.join(project_root, ".pre-commit-config.yaml")
    if os.path.exists(pre_commit_path):
        print(f"[setup_linting] {pre_commit_path} already exists. Skipping.")
    else:
        with open(pre_commit_path, "w", encoding="utf-8") as f:
            f.write(create_pre_commit_config())
        print(f"[setup_linting] Created {pre_commit_path}")

    print("[setup_linting] Linting and formatting configuration complete.")

if __name__ == "__main__":
    main()