import subprocess
import sys
from pathlib import Path
import json

def get_project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).resolve().parent.parent

def install_tools() -> None:
    """Install ruff, flake8, and black if not present."""
    tools = ["ruff", "flake8", "black"]
    for tool in tools:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", tool])
        except subprocess.CalledProcessError as e:
            print(f"Failed to install {tool}: {e}")
            raise

def ensure_config_file() -> None:
    """Create .ruff.toml and pyproject.toml (for black) if they don't exist."""
    root = get_project_root()
    
    # Create .ruff.toml
    ruff_config = root / ".ruff.toml"
    if not ruff_config.exists():
        content = """
target-version = "py38"

[lint]
select = ["E", "F", "W", "I", "N", "UP", "B", "C4", "SIM"]
ignore = ["E501", "B008"]

[lint.per-file-ignores]
"tests/*" = ["S101"]
"""
        ruff_config.write_text(content.strip())
        print(f"Created {ruff_config}")
    
    # Create pyproject.toml for Black if it doesn't exist
    pyproject = root / "pyproject.toml"
    if not pyproject.exists():
        content = """
[tool.black]
line-length = 88
target-version = ['py38']
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

[tool.ruff]
target-version = "py38"

[tool.ruff.lint]
select = ["E", "F", "W", "I", "N", "UP", "B", "C4", "SIM"]
ignore = ["E501", "B008"]
"""
        pyproject.write_text(content.strip())
        print(f"Created {pyproject}")

def run_lint_check() -> None:
    """Run ruff check on the codebase."""
    root = get_project_root()
    try:
        result = subprocess.run(
            ["ruff", "check", "code/", "tests/"],
            cwd=root,
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print("Ruff check found issues:")
            print(result.stdout)
            print(result.stderr)
            sys.exit(result.returncode)
        else:
            print("Ruff check passed.")
    except FileNotFoundError:
        print("Ruff not found. Please install it.")
        sys.exit(1)

def run_format_check() -> None:
    """Run black check on the codebase."""
    root = get_project_root()
    try:
        result = subprocess.run(
            ["black", "--check", "code/", "tests/"],
            cwd=root,
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print("Black check found formatting issues:")
            print(result.stdout)
            print(result.stderr)
            sys.exit(result.returncode)
        else:
            print("Black check passed.")
    except FileNotFoundError:
        print("Black not found. Please install it.")
        sys.exit(1)

def run_lint_fix() -> None:
    """Run ruff check with --fix on the codebase."""
    root = get_project_root()
    try:
        result = subprocess.run(
            ["ruff", "check", "--fix", "code/", "tests/"],
            cwd=root,
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print("Ruff check (with fixes) still found issues:")
            print(result.stdout)
            print(result.stderr)
        else:
            print("Ruff check and fix passed.")
    except FileNotFoundError:
        print("Ruff not found. Please install it.")
        sys.exit(1)

def run_format_fix() -> None:
    """Run black on the codebase to format files."""
    root = get_project_root()
    try:
        result = subprocess.run(
            ["black", "code/", "tests/"],
            cwd=root,
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print("Black formatting encountered errors:")
            print(result.stdout)
            print(result.stderr)
        else:
            print("Black formatting completed.")
    except FileNotFoundError:
        print("Black not found. Please install it.")
        sys.exit(1)

def main() -> None:
    """Main entry point for setup_linting script."""
    import argparse
    parser = argparse.ArgumentParser(description="Setup and run linting/formatting tools.")
    parser.add_argument("--install", action="store_true", help="Install tools.")
    parser.add_argument("--check", action="store_true", help="Run checks (lint and format).")
    parser.add_argument("--fix", action="store_true", help="Run fixes (lint and format).")
    parser.add_argument("--ensure-config", action="store_true", help="Ensure config files exist.")
    args = parser.parse_args()

    if args.install:
        install_tools()
    if args.ensure_config:
        ensure_config_file()
    if args.check:
        run_lint_check()
        run_format_check()
    if args.fix:
        run_lint_fix()
        run_format_fix()
    
    if not any([args.install, args.check, args.fix, args.ensure_config]):
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()