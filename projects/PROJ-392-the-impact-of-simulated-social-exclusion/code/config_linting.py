import os
from pathlib import Path

def ensure_code_dir():
    """Ensures the code directory exists."""
    base_dir = Path(__file__).resolve().parent.parent
    code_dir = base_dir / "code"
    code_dir.mkdir(parents=True, exist_ok=True)
    return code_dir

def write_flake8_config(code_dir):
    """Creates a .flake8 configuration file."""
    config_content = """[flake8]
max-line-length = 120
exclude = 
    .git,
    __pycache__,
    build,
    dist
ignore = E203, W503
"""
    config_path = code_dir.parent / ".flake8"
    with open(config_path, "w") as f:
        f.write(config_content)
    print(f"Created .flake8 at {config_path}")

def write_pyproject_config(code_dir):
    """Creates a pyproject.toml with Black configuration."""
    config_content = """[tool.black]
line-length = 120
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
    config_path = code_dir.parent / "pyproject.toml"
    # Check if file exists to avoid overwriting if other config is there
    if not config_path.exists():
        with open(config_path, "w") as f:
            f.write(config_content)
        print(f"Created pyproject.toml at {config_path}")
    else:
        print(f"pyproject.toml already exists at {config_path}, skipping Black config write.")

def write_editorconfig(code_dir):
    """Creates a .editorconfig file."""
    config_content = """# EditorConfig helps maintain consistent coding styles
root = true

[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true
trim_trailing_whitespace = true
indent_style = space
indent_size = 4

[*.py]
indent_size = 4
"""
    config_path = code_dir.parent / ".editorconfig"
    with open(config_path, "w") as f:
        f.write(config_content)
    print(f"Created .editorconfig at {config_path}")

def write_precommit_config(code_dir):
    """Creates a .pre-commit-config.yaml file."""
    config_content = """repos:
  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
- id: black
  language_version: python3.11
  - repo: https://github.com/pycqa/flake8
    rev: 7.0.0
    hooks:
- id: flake8
"""
    config_path = code_dir.parent / ".pre-commit-config.yaml"
    with open(config_path, "w") as f:
        f.write(config_content)
    print(f"Created .pre-commit-config.yaml at {config_path}")

def main():
    """Main entry point to set up linting and formatting configuration."""
    code_dir = ensure_code_dir()
    print("Configuring linting and formatting tools...")
    write_flake8_config(code_dir)
    write_pyproject_config(code_dir)
    write_editorconfig(code_dir)
    write_precommit_config(code_dir)
    print("Linting and formatting configuration complete.")

if __name__ == "__main__":
    main()