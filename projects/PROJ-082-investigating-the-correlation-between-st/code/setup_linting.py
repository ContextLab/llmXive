import subprocess
import sys
from pathlib import Path
import json

def get_project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).resolve().parent.parent

def install_tools() -> None:
    """Install ruff and black if not present."""
    print("Installing linting and formatting tools...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "ruff", "black"], stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError as e:
        print(f"Failed to install tools: {e}", file=sys.stderr)
        sys.exit(1)

def ensure_config_file() -> None:
    """Ensure .ruff.toml exists with basic configuration."""
    root = get_project_root()
    config_path = root / ".ruff.toml"
    if not config_path.exists():
        config_content = """
[lint]
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # Pyflakes
    "I",  # isort
    "C",  # flake8-comprehensions
    "B",  # flake8-bugbear
]
ignore = [
    "E501",  # line too long (handled by black)
    "B008",  # do not perform function calls in argument defaults
]

[format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "auto"
"""
        config_path.write_text(config_content.strip())
        print(f"Created {config_path}")

def run_lint_check() -> bool:
    """Run ruff check. Returns True if no violations, False otherwise."""
    root = get_project_root()
    try:
        result = subprocess.run(
            ["ruff", "check", str(root / "code")],
            capture_output=True,
            text=True,
            cwd=root
        )
        if result.returncode != 0:
            print("Ruff violations found:")
            print(result.stdout)
            if result.stderr:
                print(result.stderr, file=sys.stderr)
            return False
        print("No linting violations found.")
        return True
    except FileNotFoundError:
        print("ruff not found. Please install it.", file=sys.stderr)
        return False

def run_format_check() -> bool:
    """Run black check. Returns True if formatted correctly, False otherwise."""
    root = get_project_root()
    try:
        result = subprocess.run(
            ["black", "--check", str(root / "code")],
            capture_output=True,
            text=True,
            cwd=root
        )
        if result.returncode != 0:
            print("Black formatting violations found:")
            print(result.stdout)
            if result.stderr:
                print(result.stderr, file=sys.stderr)
            return False
        print("Code is properly formatted.")
        return True
    except FileNotFoundError:
        print("black not found. Please install it.", file=sys.stderr)
        return False

def run_lint_fix() -> bool:
    """Run ruff check --fix. Returns True if successful."""
    root = get_project_root()
    try:
        result = subprocess.run(
            ["ruff", "check", "--fix", str(root / "code")],
            capture_output=True,
            text=True,
            cwd=root
        )
        if result.returncode != 0:
            # Some errors might be unfixable
            print("Ruff fixed some issues, but others remain:")
            print(result.stdout)
            return False
        print("Ruff fixed all auto-fixable issues.")
        return True
    except FileNotFoundError:
        print("ruff not found.", file=sys.stderr)
        return False

def run_format_fix() -> bool:
    """Run black formatting. Returns True if successful."""
    root = get_project_root()
    try:
        result = subprocess.run(
            ["black", str(root / "code")],
            capture_output=True,
            text=True,
            cwd=root
        )
        if result.returncode != 0:
            print("Black failed to format some files:")
            print(result.stdout)
            return False
        print("Code formatted successfully.")
        return True
    except FileNotFoundError:
        print("black not found.", file=sys.stderr)
        return False

def main() -> None:
    """Main entry point for linting setup and execution."""
    parser = argparse.ArgumentParser(description="Linting and formatting tools")
    parser.add_argument("--install", action="store_true", help="Install tools")
    parser.add_argument("--config", action="store_true", help="Ensure config files exist")
    parser.add_argument("--check", action="store_true", help="Run checks only")
    parser.add_argument("--fix", action="store_true", help="Run fixers")
    parser.add_argument("--all", action="store_true", help="Run full cycle: install, config, check, fix, check")
    args = parser.parse_args()

    if args.install or args.all:
        install_tools()

    if args.config or args.all:
        ensure_config_file()

    if args.check or args.all:
        lint_ok = run_lint_check()
        fmt_ok = run_format_check()
        if not (lint_ok and fmt_ok):
            if args.fix or args.all:
                print("Fixing issues...")
                run_lint_fix()
                run_format_fix()
                print("Re-checking after fixes...")
                lint_ok = run_lint_check()
                fmt_ok = run_format_check()
            else:
                print("Violations found. Run with --fix to attempt automatic fixes.")
                sys.exit(1)
        else:
            sys.exit(0)
    elif args.fix:
        run_lint_fix()
        run_format_fix()

if __name__ == "__main__":
    main()