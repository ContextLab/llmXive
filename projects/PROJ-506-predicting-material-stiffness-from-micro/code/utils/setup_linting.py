"""
Setup and verification utilities for linting (ruff/flake8) and formatting (black).
"""
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import List, Tuple, Optional

def check_command_available(command: str) -> bool:
    """
    Check if a command-line tool is available in the environment.
    
    Args:
        command: The name of the command to check (e.g., 'ruff', 'black', 'flake8')
        
    Returns:
        True if the command is available, False otherwise.
    """
    try:
        result = subprocess.run(
            [command, "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def validate_config_files(project_root: Optional[Path] = None) -> Tuple[bool, List[str]]:
    """
    Validate that required configuration files for linting and formatting exist.
    
    Args:
        project_root: The root directory of the project. Defaults to current working directory.
        
    Returns:
        A tuple of (success: bool, messages: List[str])
        success is True if all required config files are present and valid.
    """
    if project_root is None:
        project_root = Path.cwd()
        
    messages = []
    all_valid = True
    
    # Check for pyproject.toml (preferred for ruff/black)
    pyproject_path = project_root / "pyproject.toml"
    if not pyproject_path.exists():
        messages.append("WARNING: pyproject.toml not found. Creating configuration.")
        # We will create it in main() if missing
    else:
        try:
            with open(pyproject_path, "rb") as f:
                config = tomllib.load(f)
            
            # Check for [tool.ruff] or [tool.ruff.lint]
            if "tool" not in config or "ruff" not in config["tool"]:
                messages.append("WARNING: [tool.ruff] section missing in pyproject.toml")
                all_valid = False
            else:
                messages.append("OK: [tool.ruff] found in pyproject.toml")
                
            # Check for [tool.black]
            if "tool" not in config or "black" not in config["tool"]:
                messages.append("WARNING: [tool.black] section missing in pyproject.toml")
                all_valid = False
            else:
                messages.append("OK: [tool.black] found in pyproject.toml")
                
        except Exception as e:
            messages.append(f"ERROR: Could not parse pyproject.toml: {e}")
            all_valid = False
            
    # Check for .flake8 (optional, but good to have if not using pyproject.toml for flake8)
    flake8_path = project_root / ".flake8"
    if not flake8_path.exists():
        # If using ruff, flake8 is not strictly needed, but we note it
        messages.append("INFO: .flake8 not found (ruff can replace flake8)")
        
    return all_valid, messages

def create_pyproject_config(project_root: Optional[Path] = None) -> None:
    """
    Create a pyproject.toml file with ruff and black configurations if it doesn't exist.
    
    Args:
        project_root: The root directory of the project.
    """
    if project_root is None:
        project_root = Path.cwd()
        
    pyproject_path = project_root / "pyproject.toml"
    
    # If it exists, we don't overwrite to avoid losing existing config
    if pyproject_path.exists():
        print(f"pyproject.toml already exists at {pyproject_path}. Skipping creation.")
        return
        
    config_content = """[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "llmxive-material-stiffness"
version = "0.1.0"
description = "Predicting Material Stiffness from Microstructure Images"
requires-python = ">=3.10"

[tool.black]
line-length = 88
target-version = ['py310']
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

[tool.ruff]
# Same as Black.
line-length = 88
target-version = "py310"

[tool.ruff.lint]
# Enable Pyflakes (`F`) and a subset of pycodestyle (`E`) codes.
select = ["E4", "E7", "E9", "F", "I", "UP"]
ignore = []

# Allow fix for all enabled rules (when `--fix`) is provided.
fixable = ["ALL"]
unfixable = []

# Exclude a few generated files or directories.
exclude = [
    ".bzr",
    ".direnv",
    ".eggs",
    ".git",
    ".hg",
    ".mypy_cache",
    ".nox",
    ".pants.d",
    ".pytype",
    ".ruff_cache",
    ".svn",
    ".tox",
    ".venv",
    "__pypackages__",
    "_build",
    "buck-out",
    "build",
    "dist",
    "node_modules",
    "venv",
]

# Allow unused variables when underscore-prefixed.
dummy-variable-rgx = "^(_+|(_+[a-zA-Z0-9_]*[a-zA-Z0-9]+?))$"

[tool.ruff.lint.per-file-ignores]
"__init__.py" = ["F401"]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
"""
    
    with open(pyproject_path, "w") as f:
        f.write(config_content)
        
    print(f"Created pyproject.toml at {pyproject_path} with ruff and black configurations.")

def main() -> int:
    """
    Main entry point for the setup_linting script.
    
    Checks for availability of ruff, black, and flake8.
    Validates or creates configuration files.
    
    Returns:
        0 if setup is successful, 1 otherwise.
    """
    print("=== Linting and Formatting Setup ===")
    
    # Check for tools
    tools = ["ruff", "black"]
    missing_tools = []
    
    for tool in tools:
        if check_command_available(tool):
            print(f"✓ {tool} is available.")
        else:
            print(f"✗ {tool} is NOT available.")
            missing_tools.append(tool)
            
    if missing_tools:
        print(f"\nTo install missing tools, run:")
        print(f"  pip install {' '.join(missing_tools)}")
        print("\nNote: ruff and black are not in requirements.txt yet.")
        print("Adding them to requirements.txt is recommended.")
        
    # Validate/Create config
    print("\n--- Checking Configuration ---")
    project_root = Path(__file__).resolve().parent.parent.parent
    success, messages = validate_config_files(project_root)
    
    for msg in messages:
        if msg.startswith("ERROR"):
            print(f"  {msg}")
        elif msg.startswith("WARNING"):
            print(f"  {msg}")
        elif msg.startswith("OK"):
            print(f"  {msg}")
        else:
            print(f"  {msg}")
            
    if not success or not (project_root / "pyproject.toml").exists():
        print("\n--- Creating Configuration ---")
        create_pyproject_config(project_root)
        # Re-validate
        success, messages = validate_config_files(project_root)
        for msg in messages:
            if msg.startswith("OK"):
                print(f"  {msg}")
                
    if missing_tools:
        print("\n⚠ Setup incomplete: Missing tools. Please install them manually.")
        return 1
        
    print("\n✓ Linting and formatting setup complete.")
    return 0

if __name__ == "__main__":
    sys.exit(main())