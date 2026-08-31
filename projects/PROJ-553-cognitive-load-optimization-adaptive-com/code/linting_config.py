"""
Linting and formatting configuration utilities.
Provides commands and runners for ruff and black.
"""
from pathlib import Path
import subprocess
import sys
from typing import Optional


def get_ruff_command() -> list[str]:
    """Return the ruff check command with project-specific configuration."""
    return [
        "ruff", "check",
        ".",
        "--config=pyproject.toml",
        "--output-format=full",
    ]


def get_black_command() -> list[str]:
    """Return the black formatting command with project-specific configuration."""
    return [
        "black",
        ".",
        "--config=pyproject.toml",
        "--line-length=88",
    ]


def get_format_check_command() -> list[str]:
    """Return the black check-only command."""
    return [
        "black",
        ".",
        "--config=pyproject.toml",
        "--check",
        "--line-length=88",
    ]


def get_lint_check_command() -> list[str]:
    """Return the ruff check command."""
    return get_ruff_command()


def run_formatter(path: Optional[Path] = None) -> int:
    """
    Run the black formatter on the specified path or the project root.
    Returns 0 on success, non-zero on failure.
    """
    target = str(path) if path else "."
    cmd = get_black_command()
    cmd[-2:-2] = [target]  # Insert target before flags if needed, but black accepts path at end
    # Actually, black command structure: black [options] [path]
    # Reconstruct for clarity:
    cmd = ["black", "--config=pyproject.toml", "--line-length=88", target]
    
    try:
        result = subprocess.run(cmd, check=True)
        return result.returncode
    except subprocess.CalledProcessError as e:
        return e.returncode


def run_linter(path: Optional[Path] = None) -> int:
    """
    Run the ruff linter on the specified path or the project root.
    Returns 0 on success, non-zero on failure.
    """
    target = str(path) if path else "."
    cmd = ["ruff", "check", target, "--config=pyproject.toml", "--output-format=full"]
    
    try:
        result = subprocess.run(cmd, check=True)
        return result.returncode
    except subprocess.CalledProcessError as e:
        return e.returncode


def main() -> None:
    """Entry point for CLI usage of linting tools."""
    import argparse

    parser = argparse.ArgumentParser(description="Project linting and formatting tools.")
    parser.add_argument(
        "action",
        choices=["lint", "format", "check-lint", "check-format"],
        help="Action to perform: lint (fix), format (fix), check-lint, check-format",
    )
    parser.add_argument("--path", type=Path, default=None, help="Target path (default: project root)")

    args = parser.parse_args()

    if args.action == "lint":
        code = run_linter(args.path)
    elif args.action == "format":
        code = run_formatter(args.path)
    elif args.action == "check-lint":
        code = run_linter(args.path)
    elif args.action == "check-format":
        code = run_formatter(args.path) # Note: run_formatter runs black in fix mode usually, but we can adapt or use check command
        # Correcting for check-format:
        cmd = get_format_check_command()
        if args.path:
            cmd.append(str(args.path))
        try:
            result = subprocess.run(cmd, check=True)
            code = result.returncode
        except subprocess.CalledProcessError as e:
            code = e.returncode
    else:
        code = 1

    sys.exit(code)


if __name__ == "__main__":
    main()
