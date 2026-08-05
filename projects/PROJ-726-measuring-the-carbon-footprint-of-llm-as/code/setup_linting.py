import os
import subprocess
import sys
from pathlib import Path

def write_config_file(project_root: Path, filename: str, content: str) -> None:
    """Writes a configuration file to the project root."""
    filepath = project_root / filename
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Created {filepath}")

def setup_ruff_config(project_root: Path) -> None:
    """Creates a .ruff.toml configuration file."""
    content = """[lint]
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
    "B008", # do not perform function calls in argument defaults
]

[lint.isort]
known-first-party = ["code"]

[format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "auto"
"""
    write_config_file(project_root, ".ruff.toml", content)

def setup_black_config(project_root: Path) -> None:
    """Creates a pyproject.toml section for Black configuration if not present,
    or appends the section."""
    pyproject_path = project_root / "pyproject.toml"
    
    # Read existing content if file exists
    existing_content = ""
    if pyproject_path.exists():
        with open(pyproject_path, 'r', encoding='utf-8') as f:
            existing_content = f.read()

    # Check if [tool.black] already exists
    if "[tool.black]" not in existing_content:
        black_section = """
[tool.black]
line-length = 88
target-version = ['py311']
include = '\\.pyi?$'
"""
        with open(pyproject_path, 'a', encoding='utf-8') as f:
            f.write(black_section)
        print(f"Added [tool.black] section to {pyproject_path}")
    else:
        print(f"[tool.black] section already exists in {pyproject_path}")

def run_format(project_root: Path) -> int:
    """Runs black formatter on the code directory."""
    code_dir = project_root / "code"
    if not code_dir.exists():
        print(f"Error: {code_dir} does not exist.")
        return 1

    try:
        result = subprocess.run(
            [sys.executable, "-m", "black", str(code_dir)],
            capture_output=True,
            text=True,
            check=True
        )
        print(result.stdout)
        return 0
    except subprocess.CalledProcessError as e:
        print(f"Black formatting failed:\n{e.stderr}")
        return 1
    except FileNotFoundError:
        print("Error: 'black' is not installed. Please run 'pip install black'.")
        return 1

def run_lint(project_root: Path) -> int:
    """Runs ruff linter on the code directory."""
    code_dir = project_root / "code"
    if not code_dir.exists():
        print(f"Error: {code_dir} does not exist.")
        return 1

    try:
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "check", str(code_dir)],
            capture_output=True,
            text=True,
            check=True
        )
        print(result.stdout)
        return 0
    except subprocess.CalledProcessError as e:
        print(f"Ruff linting found issues:\n{e.stdout}")
        return 1
    except FileNotFoundError:
        print("Error: 'ruff' is not installed. Please run 'pip install ruff'.")
        return 1

def main() -> None:
    """Main entry point to configure and run linting/formatting."""
    project_root = Path(__file__).resolve().parent.parent
    
    print("Configuring linting (ruff) and formatting (black)...")
    setup_ruff_config(project_root)
    setup_black_config(project_root)
    
    print("\n--- Running Formatter (Black) ---")
    format_exit_code = run_format(project_root)
    
    print("\n--- Running Linter (Ruff) ---")
    lint_exit_code = run_lint(project_root)

    if format_exit_code != 0 or lint_exit_code != 0:
        print("\nConfiguration complete, but formatting or linting found issues.")
        sys.exit(1)
    else:
        print("\nAll checks passed successfully.")
        sys.exit(0)

if __name__ == "__main__":
    main()