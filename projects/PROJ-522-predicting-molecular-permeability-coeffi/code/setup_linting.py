"""
Setup script for linting and formatting configuration.
Creates ruff and black configuration files.
"""
import os
import sys
from pathlib import Path

def create_linting_config():
    """Create ruff and black configuration files."""
    base_dir = Path(__file__).parent.parent
    code_dir = base_dir / "code"

    # Create .ruff.toml
    ruff_config = code_dir / ".ruff.toml"
    ruff_content = """
[lint]
select = ["E", "F", "W", "I", "N", "UP", "B", "C4", "ARG", "SIM"]
ignore = ["E501"]  # Line length is handled by Black
target-version = "py39"

[lint.per-file-ignores]
"__init__.py" = ["F401"]

[format]
line-length = 100
target-version = "py39"
"""
    with open(ruff_config, "w") as f:
        f.write(ruff_content.strip())
    print(f"Created: {ruff_config}")

    # Create .black.toml
    black_config = code_dir / ".black.toml"
    black_content = """
[tool.black]
line-length = 100
target-version = ['py39', 'py310', 'py311']
include = '\\.pyi?$'
exclude = '''
/(
    \\.eggs
  | \\.git
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
    with open(black_config, "w") as f:
        f.write(black_content.strip())
    print(f"Created: {black_config}")

    return True

def run_command(command):
    """Run a shell command and return the result."""
    import subprocess
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return e.returncode, e.stdout, e.stderr

def main():
    """Main entry point for the linting setup script."""
    try:
        create_linting_config()
        print("SUCCESS: Linting configuration initialized.")
        return 0
    except Exception as e:
        print(f"ERROR: Failed to initialize linting configuration: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())