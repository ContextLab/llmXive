"""
Linting and formatting configuration generation utilities.
Generates ruff.toml and pyproject.toml (for black) configuration files.
"""
import os
from pathlib import Path


def generate_ruff_config() -> str:
    """
    Generate the content for a .ruff.toml configuration file.
    Configures ruff to follow PEP 8, ignore specific safe-but-annoying rules,
    and enforce line length of 88 (standard for black compatibility).
    """
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
    "RUF", # ruff-specific rules
]
ignore = [
    "E501", # line-too-long (handled by black)
    "B008", # do-not-perform-argument-assignment-in-function-signature (common in data classes)
    "RUF012", # mutable-class-defaults (often used in pydantic/dataclasses)
]

[lint.isort]
known-first-party = ["code"]
force-sort-within-sections = true

[format]
quote-style = "double"
indent-style = "space"
line-ending = "auto"
skip-magic-trailing-comma = false
"""


def generate_black_config() -> str:
    """
    Generate the [tool.black] section content for pyproject.toml.
    """
    return """[tool.black]
line-length = 88
target-version = ['py311']
include = '\\.pyi?$'
extend-exclude = '''
/(
    # The following are specific to Black, you probably don't want those.
    | build
    | dist
    | venv
    | .venv
    | .tox
)/
'''
"""


def setup_linting_files(base_dir: Path) -> None:
    """
    Create configuration files for ruff and black in the project root.
    
    Args:
        base_dir: The root directory of the project where config files should be written.
    """
    # Ensure base directory exists
    base_dir.mkdir(parents=True, exist_ok=True)

    # Write .ruff.toml
    ruff_path = base_dir / ".ruff.toml"
    ruff_content = generate_ruff_config()
    with open(ruff_path, "w", encoding="utf-8") as f:
        f.write(ruff_content)
    print(f"Created: {ruff_path}")

    # Write/Update pyproject.toml for Black
    pyproject_path = base_dir / "pyproject.toml"
    black_content = generate_black_config()
    
    if pyproject_path.exists():
        # Read existing content
        existing = pyproject_path.read_text(encoding="utf-8")
        # Simple check to avoid duplicating [tool.black] if it exists
        if "[tool.black]" not in existing:
            # Append if file doesn't end with newline
            if existing and not existing.endswith("\n"):
                existing += "\n"
            existing += "\n" + black_content
            pyproject_path.write_text(existing, encoding="utf-8")
            print(f"Updated: {pyproject_path} (added [tool.black])")
        else:
            print(f"Skipped: {pyproject_path} ([tool.black] already exists)")
    else:
        pyproject_path.write_text(black_content, encoding="utf-8")
        print(f"Created: {pyproject_path}")


def main() -> None:
    """
    Entry point for setting up linting configuration.
    Detects the project root and creates configuration files.
    """
    # Determine project root (assume script is in code/utils/, go up two levels)
    # Or use current working directory if running from root
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent.parent

    print(f"Setting up linting configuration in: {project_root}")
    setup_linting_files(project_root)
    print("Linting configuration complete.")
    print("\nTo use:")
    print("  ruff check .          # Run linter")
    print("  ruff format .         # Run formatter (if using ruff's formatter)")
    print("  black .               # Run black formatter")
    print("  ruff check --fix .    # Auto-fix issues")