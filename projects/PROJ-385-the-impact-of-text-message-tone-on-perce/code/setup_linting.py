"""
Setup script for linting (ruff) and formatting (black) tools.
This script installs the tools and generates configuration files if they don't exist.
"""
import subprocess
import sys
from pathlib import Path

def check_tool(tool_name: str) -> bool:
    """Check if a tool is installed."""
    try:
        subprocess.run([sys.executable, "-m", tool_name, "--version"], check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError:
        return False

def install_tools():
    """Install ruff and black."""
    print("Installing ruff and black...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "ruff", "black"])
    print("Installation complete.")

def check_config_files(code_dir: Path):
    """Check if configuration files exist."""
    ruff_config = code_dir / ".ruff.toml"
    black_config = code_dir / "pyproject.toml"

    if not ruff_config.exists():
        print(f"Warning: {ruff_config} not found. Creating default configuration...")
        create_ruff_config(code_dir)

    if not black_config.exists():
        print(f"Warning: {black_config} not found. Creating default configuration...")
        create_black_config(code_dir)
    else:
        # Check if pyproject.toml has [tool.black] section
        with open(black_config, "r") as f:
            content = f.read()
            if "[tool.black]" not in content:
                print(f"Warning: {black_config} exists but missing [tool.black] section. Appending configuration...")
                with open(black_config, "a") as append_file:
                    append_file.write("\n[tool.black]\nline-length = 88\ntarget-version = ['py38']\n")

def create_ruff_config(code_dir: Path):
    """Create a default .ruff.toml configuration file."""
    config_content = """[lint]
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
    "E501", # line too long (handled by black)
]
exclude = [
    ".git",
    "__pycache__",
    "build",
    "dist",
]

[lint.isort]
known-first-party = ["config", "logging_config", "setup_data_dirs", "setup_linting", "setup_project_structure", "validate_schemas", "verify_logging"]
"""
    with open(code_dir / ".ruff.toml", "w") as f:
        f.write(config_content)
    print(f"Created {code_dir / '.ruff.toml'}")

def create_black_config(code_dir: Path):
    """Create a default pyproject.toml configuration file for black."""
    config_content = """[tool.black]
line-length = 88
target-version = ['py38']
include = '\\.pyi?$'
exclude = '''
/(
    \\.git
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
    with open(code_dir / "pyproject.toml", "w") as f:
        f.write(config_content)
    print(f"Created {code_dir / 'pyproject.toml'}")

def main():
    """Main entry point for setup_linting."""
    code_dir = Path(__file__).parent

    # Install tools if not present
    if not check_tool("ruff"):
        install_tools()
    elif not check_tool("black"):
        install_tools()

    # Check and create configuration files
    check_config_files(code_dir)

    print("Linting and formatting setup complete.")
    print("To run linting: ruff check .")
    print("To run formatting: black .")
    print("To run both: python code/06_run_linting.py")

if __name__ == "__main__":
    main()
