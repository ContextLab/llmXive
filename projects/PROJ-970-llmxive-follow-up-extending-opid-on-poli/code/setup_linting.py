import os
import sys

def create_ruff_config() -> None:
    """Create a ruff.toml configuration file."""
    base_dir = os.getcwd()
    file_path = os.path.join(base_dir, "ruff.toml")
    
    content = """[lint]
select = ["E", "F", "W", "I", "N", "UP", "B", "C4", "SIM"]
ignore = ["E501", "B008"]

[lint.per-file-ignores]
"tests/*" = ["S101"]

[format]
quote-style = "double"
indent-style = "space"
line-ending = "auto"
"""
    
    with open(file_path, "w") as f:
        f.write(content)
    
    print(f"Created ruff.toml at {file_path}")

def create_black_config() -> None:
    """Create a .black.toml or add to pyproject.toml (handled in setup_project)."""
    # Black config is usually in pyproject.toml, which is created by setup_project.py
    # This function exists for completeness if a separate config is needed later
    pass

def create_pre_commit_config() -> None:
    """Create a .pre-commit-config.yaml file."""
    base_dir = os.getcwd()
    file_path = os.path.join(base_dir, ".pre-commit-config.yaml")
    
    content = """repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.3.0
    hooks:
- id: ruff
  args: [--fix]
- id: ruff-format
  - repo: https://github.com/psf/black
    rev: 24.3.0
    hooks:
- id: black
"""
    
    with open(file_path, "w") as f:
        f.write(content)
    
    print(f"Created .pre-commit-config.yaml at {file_path}")

def main() -> None:
    """Main entry point to set up linting and formatting tools."""
    print("Setting up linting and formatting configurations...")
    create_ruff_config()
    create_pre_commit_config()
    print("Linting setup complete.")

if __name__ == "__main__":
    main()