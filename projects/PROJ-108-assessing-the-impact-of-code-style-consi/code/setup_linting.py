import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd: list, description: str) -> bool:
    """
    Run a shell command and return True if successful.
    """
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running {description}: {e}")
        print(f"Stderr: {e.stderr}")
        return False

def main():
    """
    Configure linting (flake8) and formatting (black) tools.
    This script installs the tools and creates configuration files.
    """
    project_root = Path(__file__).resolve().parent.parent
    code_dir = project_root / "code"
    
    # Ensure code directory exists
    code_dir.mkdir(parents=True, exist_ok=True)

    # 1. Install dependencies
    print("Installing linting and formatting tools...")
    install_success = run_command(
        [sys.executable, "-m", "pip", "install", "flake8", "black"],
        "Installing flake8 and black"
    )
    
    if not install_success:
        print("Failed to install dependencies. Please install manually: pip install flake8 black")
        sys.exit(1)

    # 2. Create .flake8 configuration
    flake8_config_path = project_root / ".flake8"
    flake8_content = """[flake8]
max-line-length = 88
exclude = .git,__pycache__,build,dist,.eggs
extend-ignore = E203, W503
max-complexity = 10
"""
    print(f"Creating {flake8_config_path}...")
    with open(flake8_config_path, "w") as f:
        f.write(flake8_content)

    # 3. Create pyproject.toml for Black configuration
    pyproject_path = project_root / "pyproject.toml"
    # Check if it exists to avoid overwriting other configs if any
    if not pyproject_path.exists():
        print(f"Creating {pyproject_path}...")
        pyproject_content = """[tool.black]
line-length = 88
target-version = ['py310']
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
        with open(pyproject_path, "w") as f:
            f.write(pyproject_content)
    else:
        print(f"{pyproject_path} already exists. Skipping Black config creation.")

    # 4. Create .gitignore updates if necessary (optional but good practice)
    gitignore_path = project_root / ".gitignore"
    gitignore_entries = [
        "__pycache__/",
        "*.py[cod]",
        "*$py.class",
        ".eggs/",
        "*.egg-info/",
        "dist/",
        "build/",
        ".mypy_cache/",
        ".pytest_cache/",
        ".coverage",
        "htmlcov/",
        ".tox/",
        "venv/",
        ".venv/",
        "env/",
    ]
    
    if gitignore_path.exists():
        with open(gitignore_path, "r") as f:
            existing_lines = set(f.read().splitlines())
    
        new_entries = [line for line in gitignore_entries if line not in existing_lines]
        if new_entries:
            print(f"Updating {gitignore_path}...")
            with open(gitignore_path, "a") as f:
                f.write("\n# Linting/Testing artifacts\n")
                for entry in new_entries:
                    f.write(entry + "\n")
        else:
            print(f"{gitignore_path} already contains linting entries.")
    else:
        print(f"Creating {gitignore_path}...")
        with open(gitignore_path, "w") as f:
            f.write("# Linting/Testing artifacts\n")
            for entry in gitignore_entries:
                f.write(entry + "\n")

    print("\nLinting and formatting configuration complete.")
    print("To run linter:   flake8 code/")
    print("To run formatter: black code/")

if __name__ == "__main__":
    main()