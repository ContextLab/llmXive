"""
Setup script for linting (ruff) and formatting (black) tools.
Generates configuration files and a helper script to run checks.
"""
import os
import sys
import subprocess
from pathlib import Path

def ensure_directory_exists(path: str) -> bool:
    """Create directory if it doesn't exist."""
    try:
        Path(path).mkdir(parents=True, exist_ok=True)
        return True
    except OSError as e:
        print(f"Error creating directory {path}: {e}")
        return False

def write_config_file(filename: str, content: str) -> bool:
    """Write content to a file."""
    try:
        Path(filename).write_text(content, encoding="utf-8")
        return True
    except OSError as e:
        print(f"Error writing file {filename}: {e}")
        return False

def main():
    """Main entry point to configure ruff and black."""
    project_root = Path(__file__).parent.parent
    print(f"Configuring linting and formatting for project at: {project_root}")

    # 1. Create ruff.toml configuration
    ruff_config = """
[lint]
# Enable pycodestyle (`E`), Pyflakes (`F`), and isort (`I`)
select = ["E", "F", "I"]
ignore = []

# Allow autofix for all enabled rules (when `--fix` is provided)
fixable = ["ALL"]
unfixable = []

# Exclude a few generated directories
exclude = [
    ".git",
    ".tox",
    "__pycache__",
    "build",
    "dist",
]

# Same as Black.
line-length = 88

# Allow unused variables when underscore-prefixed.
dummy-variable-rgx = "^(_+|(_+[a-zA-Z0-9_]*[a-zA-Z0-9]+?))$"

# Assume Python 3.11
target-version = "py311"

[format]
# Same as Black.
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "auto"
"""
    
    if not write_config_file(str(project_root / "ruff.toml"), ruff_config):
        return False
    print("Created ruff.toml")

    # 2. Create pyproject.toml for Black configuration (if not exists, or append)
    # We will create a minimal one if it doesn't exist, or update it.
    # For safety in this task, we ensure the [tool.black] section exists.
    pyproject_path = project_root / "pyproject.toml"
    
    black_section = """
[tool.black]
line-length = 88
target-version = ['py311']
include = '\\.pyi?$'
exclude = '''
/(
    \.git
  | \.tox
  | __pycache__
  | build
  | dist
)/
'''
"""
    
    if pyproject_path.exists():
        content = pyproject_path.read_text(encoding="utf-8")
        if "[tool.black]" not in content:
            with open(pyproject_path, "a", encoding="utf-8") as f:
                f.write("\n" + black_section)
            print("Appended [tool.black] to pyproject.toml")
        else:
            print("pyproject.toml already contains [tool.black]")
    else:
        with open(pyproject_path, "w", encoding="utf-8") as f:
            f.write("[build-system]\nrequires = [\"setuptools>=61.0\"]\nbuild-backend = \"setuptools.build_meta\"\n\n" + black_section)
        print("Created pyproject.toml with [tool.black]")

    # 3. Create a helper script to run checks
    # We create a Python script that invokes ruff and black via subprocess
    # to ensure the environment has the tools installed.
    check_script_path = project_root / "scripts" / "run_lint_format.py"
    ensure_directory_exists(str(check_script_path.parent))
    
    check_script_content = """
import subprocess
import sys
from pathlib import Path

def run_command(cmd: list[str], description: str) -> bool:
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    try:
  result = subprocess.run(cmd, check=True, capture_output=True, text=True)
  if result.stdout:
      print(result.stdout)
  if result.stderr:
      print(result.stderr)
  print(f"✓ {description} passed")
  return True
    except subprocess.CalledProcessError as e:
  print(f"✗ {description} failed")
  if e.stdout:
      print(e.stdout)
  if e.stderr:
      print(e.stderr)
  return False

def main():
    root = Path(__file__).parent.parent
    code_dir = root / "code"
    
    # Check if tools are installed
    try:
  import ruff
  import black
    except ImportError:
  print("Error: 'ruff' or 'black' not installed. Please run: pip install ruff black")
  sys.exit(1)

    success = True

    # Run Ruff Check (Linting)
    success &= run_command(
  [sys.executable, "-m", "ruff", "check", str(code_dir)],
  "Ruff Check"
    )

    # Run Black Check (Formatting - check only, no write)
    success &= run_command(
  [sys.executable, "-m", "black", "--check", "--diff", str(code_dir)],
  "Black Check"
    )

    if success:
  print("\\nAll linting and formatting checks passed.")
  sys.exit(0)
    else:
  print("\\nSome checks failed.")
  sys.exit(1)

if __name__ == "__main__":
    main()
"""
    
    if not write_config_file(str(check_script_path), check_script_content):
        return False
    print(f"Created {check_script_path}")

    print("\nLinting (ruff) and Formatting (black) configuration complete.")
    print("To run checks: python scripts/run_lint_format.py")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)