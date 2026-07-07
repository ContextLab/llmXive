"""
Configuration and helper utilities for linting and formatting tools.
This module ensures consistency between flake8 and black configurations.
"""
import subprocess
import sys
from pathlib import Path


def run_lint() -> int:
    """Run flake8 on the code directory."""
    code_dir = Path(__file__).parent
    try:
        result = subprocess.run(
            [sys.executable, "-m", "flake8", str(code_dir)],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        return result.returncode
    except FileNotFoundError:
        print("Error: flake8 not found. Run: pip install flake8", file=sys.stderr)
        return 1


def run_format() -> int:
    """Run black on the code directory."""
    code_dir = Path(__file__).parent
    try:
        result = subprocess.run(
            [sys.executable, "-m", "black", "--check", str(code_dir)],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        return result.returncode
    except FileNotFoundError:
        print("Error: black not found. Run: pip install black", file=sys.stderr)
        return 1


def format_all() -> int:
    """Run black to format files in the code directory."""
    code_dir = Path(__file__).parent
    try:
        result = subprocess.run(
            [sys.executable, "-m", "black", str(code_dir)],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        return result.returncode
    except FileNotFoundError:
        print("Error: black not found. Run: pip install black", file=sys.stderr)
        return 1


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Linting and formatting utilities")
    parser.add_argument(
        "--lint", action="store_true", help="Run flake8 linting"
    )
    parser.add_argument(
        "--format-check", action="store_true", help="Check formatting with black"
    )
    parser.add_argument(
        "--format", action="store_true", help="Format files with black"
    )
    parser.add_argument(
        "--all", action="store_true", help="Run lint and format check"
    )

    args = parser.parse_args()

    if args.all:
        code_dir = Path(__file__).parent
        lint_result = subprocess.run(
            [sys.executable, "-m", "flake8", str(code_dir)],
            check=False,
            capture_output=True,
            text=True,
        )
        if lint_result.stdout:
            print(lint_result.stdout)
        if lint_result.stderr:
            print(lint_result.stderr, file=sys.stderr)

        format_result = subprocess.run(
            [sys.executable, "-m", "black", "--check", str(code_dir)],
            check=False,
            capture_output=True,
            text=True,
        )
        if format_result.stdout:
            print(format_result.stdout)
        if format_result.stderr:
            print(format_result.stderr, file=sys.stderr)

        sys.exit(lint_result.returncode or format_result.returncode)
    elif args.lint:
        sys.exit(run_lint())
    elif args.format_check:
        sys.exit(run_format())
    elif args.format:
        sys.exit(format_all())
    else:
        parser.print_help()
        sys.exit(0)