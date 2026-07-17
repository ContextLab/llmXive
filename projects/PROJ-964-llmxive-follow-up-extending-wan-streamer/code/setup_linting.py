import os
import sys
from pathlib import Path

def ensure_ruff_config(project_root: Path) -> None:
    """
    Create or update .ruff.toml (or ruff.toml) in the project root.
    This config enforces linting rules suitable for research code.
    """
    ruff_config_path = project_root / ".ruff.toml"
    if ruff_config_path.exists():
        # In a real implementation, we might check if it matches our desired config.
        # For now, we assume existing is okay or we overwrite to ensure consistency.
        print(f"Ruff config already exists at {ruff_config_path}")
        return

    config_content = """
    # Ruff configuration for llmXive project
    target-version = "py310"
    line-length = 88

    [lint]
    select = [
        "E",  # pycodestyle errors
        "W",  # pycodestyle warnings
        "F",  # Pyflakes
        "I",  # isort
        "C",  # flake8-comprehensions
        "B",  # flake8-bugbear
        "UP", # pyupgrade
    ]
    ignore = [
        "E501", # line too long (handled by black)
        "B008", # do not perform function calls in argument defaults (common in data pipelines)
        "C901", # too complex (research code often has complex logic)
    ]

    [lint.per-file-ignores]
    "tests/*" = ["S101"] # assertions allowed in tests

    [lint.isort]
    known-first-party = ["code"]
    """

    with open(ruff_config_path, "w", encoding="utf-8") as f:
        f.write(config_content.strip())
    print(f"Created Ruff config at {ruff_config_path}")


def ensure_black_config(project_root: Path) -> None:
    """
    Create or update pyproject.toml with Black configuration in the project root.
    """
    pyproject_path = project_root / "pyproject.toml"
    
    # Check if pyproject.toml exists and has a [tool.black] section
    if pyproject_path.exists():
        content = pyproject_path.read_text(encoding="utf-8")
        if "[tool.black]" in content:
            print(f"Black config already exists in {pyproject_path}")
            return

    # Read existing content or start empty
    existing_content = ""
    if pyproject_path.exists():
        existing_content = pyproject_path.read_text(encoding="utf-8")

    # Append Black configuration
    black_section = """

    [tool.black]
    line-length = 88
    target-version = ['py310']
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

    new_content = existing_content + black_section
    
    with open(pyproject_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    
    print(f"Updated Black config in {pyproject_path}")


def main() -> None:
    """
    Entry point to configure linting and formatting tools for the project.
    """
    # Determine project root: assume script is in code/ directory
    # and project root is parent of code/
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent

    print(f"Configuring linting and formatting in: {project_root}")

    ensure_ruff_config(project_root)
    ensure_black_config(project_root)

    print("Linting and formatting configuration complete.")
    print("\nNext steps:")
    print("  1. Install dependencies: pip install ruff black")
    print("  2. Format code: black code/")
    print("  3. Lint code: ruff check code/")

    # Optional: Create a pre-commit config if not exists
    precommit_path = project_root / ".pre-commit-config.yaml"
    if not precommit_path.exists():
        precommit_content = """
    repos:
      - repo: https://github.com/psf/black
        rev: 24.3.0
        hooks:
          - id: black
            language_version: python3.10
      - repo: https://github.com/astral-sh/ruff-pre-commit
        rev: v0.3.5
        hooks:
          - id: ruff
            args: [--fix]
    """
        with open(precommit_path, "w", encoding="utf-8") as f:
            f.write(precommit_content.strip())
        print(f"Created pre-commit config at {precommit_path}")
        print("  4. Install pre-commit hooks: pre-commit install")


if __name__ == "__main__":
    main()
