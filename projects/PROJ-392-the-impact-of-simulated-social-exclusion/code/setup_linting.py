import os
import sys
from pathlib import Path

def ensure_code_dir() -> Path:
    """Ensure the code directory exists."""
    code_dir = Path("code")
    code_dir.mkdir(exist_ok=True)
    return code_dir

def write_flake8_config() -> None:
    """Write .flake8 configuration file."""
    config_content = """[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude =
    .git,
    __pycache__,
    build,
    dist,
    .eggs,
    *.egg-info
max-complexity = 10
"""
    path = Path(".flake8")
    path.write_text(config_content)
    print(f"Created {path}")

def write_pyproject_config() -> None:
    """Write pyproject.toml with Black configuration."""
    config_content = """[tool.black]
line-length = 88
target-version = ['py311']
include = '\\.pyi?$'
exclude = '''
/(
    \\.git
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
    path = Path("pyproject.toml")
    # Append to existing if exists, otherwise create
    if path.exists():
        current = path.read_text()
        if "[tool.black]" not in current:
            path.write_text(current + "\n" + config_content)
        else:
            print(f"{path} already contains Black config, skipping.")
    else:
        path.write_text(config_content)
        print(f"Created {path}")

def write_editorconfig() -> None:
    """Write .editorconfig file."""
    config_content = """root = true

[*]
indent_style = space
indent_size = 4
end_of_line = lf
charset = utf-8
trim_trailing_whitespace = true
insert_final_newline = true

[*.{py,md}]
indent_size = 4

[*.toml]
indent_size = 2
"""
    path = Path(".editorconfig")
    path.write_text(config_content)
    print(f"Created {path}")

def write_precommit_config() -> None:
    """Write .pre-commit-config.yaml."""
    config_content = """repos:
  - repo: https://github.com/psf/black
    rev: 24.3.0
    hooks:
- id: black
  language_version: python3.11
  - repo: https://github.com/pycqa/flake8
    rev: 7.0.0
    hooks:
- id: flake8
  args: [--config=.flake8]
"""
    path = Path(".pre-commit-config.yaml")
    path.write_text(config_content)
    print(f"Created {path}")

def main() -> None:
    """Main entry point for linting setup."""
    print("Setting up linting and formatting tools...")
    ensure_code_dir()
    write_flake8_config()
    write_pyproject_config()
    write_editorconfig()
    write_precommit_config()
    print("Linting configuration complete.")

if __name__ == "__main__":
    main()