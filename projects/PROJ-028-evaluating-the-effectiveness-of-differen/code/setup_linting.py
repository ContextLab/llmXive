"""Configure linting (ruff) and formatting (black) tools for the project.

Creates/updates the configuration files at the project root:
  - ruff.toml        (ruff linter configuration)
  - pyproject.toml   (black formatter configuration)
  - .pre-commit-config.yaml (git hook integration for ruff + black)

Idempotent: re-running overwrites the config files with the canonical
configuration used by this project.
"""

from pathlib import Path

from llmxive_toolkit import paths

RUFF_CONFIG = """\
# Ruff linter configuration for the prompting-strategies evaluation project.
# Docs: https://beta.ruff.rs/docs/configuration/

target-version = "py311"
line-length = 100

[lint]
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort (import ordering)
    "B",   # flake8-bugbear
    "UP",  # pyupgrade
]
ignore = [
    "E501",  # line length handled by black / line-length above where possible
]

[lint.isort]
known-first-party = ["src", "tests"]

[format]
quote-style = "double"
indent-style = "space"
"""

PYPROJECT_CONFIG = """\
[tool.black]
target-version = ["py311"]
line-length = 100
include = '\\.pyi?$'
extend-exclude = '''(
    /(\\.eggs|\\.git|\\.hg|\\.mypy_cache|\\.tox|\\.venv|venv|_build|buck-out|build|dist)/
)'''

[tool.ruff]
target-version = "py311"
line-length = 100
"""

PRE_COMMIT_CONFIG = """\
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.4.4
    hooks:
      - id: ruff
        args: [--fix]
  - repo: https://github.com/psf/black
    rev: 24.4.2
    hooks:
      - id: black
"""

def create_config_files() -> None:
    """Create ruff and black configuration files in the project root."""
    root = Path(paths.root)

    (root / "ruff.toml").write_text(RUFF_CONFIG, encoding="utf-8")
    (root / "pyproject.toml").write_text(PYPROJECT_CONFIG, encoding="utf-8")
    (root / ".pre-commit-config.yaml").write_text(PRE_COMMIT_CONFIG, encoding="utf-8")

    print(f"Wrote {root / 'ruff.toml'}")
    print(f"Wrote {root / 'pyproject.toml'}")
    print(f"Wrote {root / '.pre-commit-config.yaml'}")

def main() -> int:
    create_config_files()
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
