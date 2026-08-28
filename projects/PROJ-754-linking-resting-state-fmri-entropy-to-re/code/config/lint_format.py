import subprocess
import sys
import argparse
from pathlib import Path

def run_command(cmd: list[str], cwd: Optional[Path] = None) -> int:
    """Run a command and return the exit code."""
    try:
        result = subprocess.run(cmd, cwd=cwd, check=False)
        return result.returncode
    except FileNotFoundError:
        print(f"Command not found: {cmd[0]}", file=sys.stderr)
        return 127

def check_ruff_installed() -> bool:
    """Check if ruff is installed."""
    return run_command(["ruff", "--version"]) == 0

def check_black_installed() -> bool:
    """Check if black is installed."""
    return run_command(["black", "--version"]) == 0

def run_lint_check(cwd: Optional[Path] = None) -> int:
    """Run ruff lint check."""
    if not check_ruff_installed():
        print("ruff is not installed. Install it via: pip install ruff", file=sys.stderr)
        return 1
    return run_command(["ruff", "check", "."], cwd=cwd)

def run_format_check(cwd: Optional[Path] = None) -> int:
    """Run black format check."""
    if not check_black_installed():
        print("black is not installed. Install it via: pip install black", file=sys.stderr)
        return 1
    return run_command(["black", "--check", "."], cwd=cwd)

def run_lint_fix(cwd: Optional[Path] = None) -> int:
    """Run ruff lint fix."""
    if not check_ruff_installed():
        print("ruff is not installed. Install it via: pip install ruff", file=sys.stderr)
        return 1
    return run_command(["ruff", "check", ".", "--fix"], cwd=cwd)

def run_format_fix(cwd: Optional[Path] = None) -> int:
    """Run black format fix."""
    if not check_black_installed():
        print("black is not installed. Install it via: pip install black", file=sys.stderr)
        return 1
    return run_command(["black", "."], cwd=cwd)

def main() -> None:
    """CLI entry point for linting and formatting."""
    parser = argparse.ArgumentParser(description="Lint and Format tools")
    parser.add_argument("--lint-check", action="store_true", help="Run lint check")
    parser.add_argument("--format-check", action="store_true", help="Run format check")
    parser.add_argument("--lint-fix", action="store_true", help="Run lint fix")
    parser.add_argument("--format-fix", action="store_true", help="Run format fix")
    args = parser.parse_args()

    if not any([args.lint_check, args.format_check, args.lint_fix, args.format_fix]):
        parser.print_help()
        sys.exit(0)

    cwd = Path(__file__).resolve().parent.parent.parent

    if args.lint_check:
        sys.exit(run_lint_check(cwd))
    if args.format_check:
        sys.exit(run_format_check(cwd))
    if args.lint_fix:
        sys.exit(run_lint_fix(cwd))
    if args.format_fix:
        sys.exit(run_format_fix(cwd))

if __name__ == "__main__":
    main()
