import subprocess
import sys
import tomllib
from pathlib import Path
from typing import List, Tuple, Optional

def check_command_available(cmd: str) -> bool:
    """Check if a command is available in the system PATH."""
    try:
        subprocess.run([cmd, "--version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def create_pyproject_config() -> bool:
    """Create or update pyproject.toml with ruff and black configuration."""
    config_path = Path("pyproject.toml")
    config_content = """
[tool.ruff]
select = ["E", "F", "W", "I", "N"]
ignore = []
line-length = 88
target-version = "py39"

[tool.black]
line-length = 88
target-version = ['py39']
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

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
"""
    with open(config_path, "w") as f:
        f.write(config_content.strip())
    return True

def validate_config_files() -> Tuple[bool, List[str]]:
    """Validate that configuration files are present and non-empty."""
    errors = []
    config_path = Path("pyproject.toml")
    if not config_path.exists():
        errors.append("pyproject.toml is missing")
    else:
        try:
            with open(config_path, "rb") as f:
                data = tomllib.load(f)
            if "tool" not in data:
                errors.append("pyproject.toml does not contain [tool] section")
            if "ruff" not in data.get("tool", {}):
                errors.append("pyproject.toml does not contain [tool.ruff] section")
            if "black" not in data.get("tool", {}):
                errors.append("pyproject.toml does not contain [tool.black] section")
        except Exception as e:
            errors.append(f"Failed to parse pyproject.toml: {e}")
    return len(errors) == 0, errors

def main():
    print("Setting up linting and formatting...")
    
    # Check commands
    ruff_ok = check_command_available("ruff")
    black_ok = check_command_available("black")
    
    if not ruff_ok or not black_ok:
        print("Warning: ruff or black not found. Please install them via pip.")
        print("  pip install ruff black")
    
    # Create config
    print("Creating pyproject.toml configuration...")
    create_pyproject_config()
    
    # Validate
    success, errors = validate_config_files()
    if success:
        print("✅ Configuration validated successfully.")
        if ruff_ok:
            print("Running 'ruff check .'...")
            try:
                subprocess.run(["ruff", "check", "."], check=False)
            except Exception as e:
                print(f"Note: ruff check failed (expected for initial state): {e}")
        if black_ok:
            print("Running 'black --check .'...")
            try:
                subprocess.run(["black", "--check", "."], check=False)
            except Exception as e:
                print(f"Note: black check failed (expected for initial state): {e}")
        sys.exit(0)
    else:
        print(f"❌ Configuration validation failed: {errors}")
        sys.exit(1)

if __name__ == "__main__":
    main()