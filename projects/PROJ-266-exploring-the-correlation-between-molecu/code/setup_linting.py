"""
Script to configure linting (flake8) and formatting (black) tools.
Creates configuration files and runs initial checks.
"""
import os
import sys
from pathlib import Path
from typing import List, Tuple

def get_project_root() -> Path:
    """Get the project root directory."""
    current = Path(__file__).resolve()
    # Traverse up until we find a marker or hit root
    while current.parent != current:
        if (current / ".git").exists():
            return current
        current = current.parent
    # Fallback to current directory if no .git found
    return Path.cwd()

def check_config_files(project_root: Path) -> Tuple[bool, List[str]]:
    """Check if configuration files exist."""
    missing = []
    flake8_config = project_root / ".flake8"
    black_config = project_root / "pyproject.toml"

    if not flake8_config.exists():
        missing.append(".flake8")
    if not black_config.exists() or "[tool.black]" not in black_config.read_text():
        missing.append("pyproject.toml (black section)")

    return len(missing) == 0, missing

def create_flake8_config(project_root: Path) -> None:
    """Create .flake8 configuration file."""
    flake8_content = """[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude =
    .git,
    __pycache__,
    build,
    dist,
    .eggs,
    *.egg-info,
    data/
per-file-ignores =
    # Allow unused imports in __init__.py
    */__init__.py:F401
    # Allow print statements in scripts
    code/data/*.py:T201
    code/utils/*.py:T201
"""
    flake8_path = project_root / ".flake8"
    flake8_path.write_text(flake8_content)
    print(f"Created {flake8_path}")

def create_black_config(project_root: Path) -> None:
    """Create/update pyproject.toml with black configuration."""
    pyproject_path = project_root / "pyproject.toml"

    black_section = """
[tool.black]
line-length = 88
target-version = ['py38', 'py39', 'py310', 'py311']
include = '\\.pyi?$'
extend-exclude = '''
/(
    \.git
  | __pycache__
  | build
  | dist
  | \.eggs
  | \.egg-info
  | data
)/
'''
"""

    if pyproject_path.exists():
        content = pyproject_path.read_text()
        if "[tool.black]" not in content:
            content = content.rstrip() + "\n" + black_section
            pyproject_path.write_text(content)
            print(f"Updated {pyproject_path} with black configuration")
        else:
            print(f"{pyproject_path} already contains black configuration")
    else:
        pyproject_path.write_text(black_section)
        print(f"Created {pyproject_path} with black configuration")

def run_flake8_check(project_root: Path) -> int:
    """Run flake8 check on the project."""
    import subprocess

    flake8_path = project_root / ".flake8"
    if not flake8_path.exists():
        print("Error: .flake8 configuration not found. Run create_flake8_config first.")
        return 1

    try:
        result = subprocess.run(
            ["flake8", "code"],
            cwd=project_root,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("✓ Flake8 check passed")
            return 0
        else:
            print("✗ Flake8 check found issues:")
            print(result.stdout)
            print(result.stderr)
            return result.returncode
    except FileNotFoundError:
        print("Error: flake8 not found. Install it with: pip install flake8")
        return 1

def run_black_check(project_root: Path) -> int:
    """Run black check on the project."""
    import subprocess

    pyproject_path = project_root / "pyproject.toml"
    if not pyproject_path.exists() or "[tool.black]" not in pyproject_path.read_text():
        print("Error: pyproject.toml with black configuration not found.")
        return 1

    try:
        result = subprocess.run(
            ["black", "--check", "code"],
            cwd=project_root,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("✓ Black check passed")
            return 0
        else:
            print("✗ Black check found files that need formatting:")
            print(result.stdout)
            print(result.stderr)
            return result.returncode
    except FileNotFoundError:
        print("Error: black not found. Install it with: pip install black")
        return 1

def main() -> None:
    """Main function to configure and check linting/formatting."""
    project_root = get_project_root()
    print(f"Project root: {project_root}")

    # Create configuration files if they don't exist
    is_complete, missing = check_config_files(project_root)
    if not is_complete:
        print("Missing configuration files:")
        for item in missing:
            print(f"  - {item}")
        print("\nCreating missing configuration files...")

        if ".flake8" in missing:
            create_flake8_config(project_root)
        if "pyproject.toml (black section)" in missing:
            create_black_config(project_root)

        print("\nConfiguration files created.")
    else:
        print("Configuration files already exist.")

    print("\nRunning linting and formatting checks...")
    flake8_exit = run_flake8_check(project_root)
    black_exit = run_black_check(project_root)

    if flake8_exit == 0 and black_exit == 0:
        print("\n✓ All checks passed! Linting and formatting are configured.")
        sys.exit(0)
    else:
        print("\n✗ Some checks failed. Please fix the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main()